#!/usr/bin/env python3
"""
Simplified latency testing for YOLO-World and small LLMs.
- Keeps HF snapshot download support for GGUF files.
- Prefers streaming generation (Qwen will stream).
- Removes extensive fallback/diagnostic noise; keeps things minimal and readable.
"""

import time
import torch
from ultralytics import YOLO
from PIL import Image
import json
from pathlib import Path
import os

# Suppress verbose output from ultralytics
import logging
logging.getLogger("ultralytics").setLevel(logging.ERROR)

try:
    from llama_cpp import Llama
except Exception:
    Llama = None


def resolve_llm_model_path(identifier: str, force_download: bool = False) -> str:
    """Resolve an identifier to a local model file path.

    Supports:
      - local filesystem paths
      - Hugging Face repo ids with optional filename hint: "owner/repo::file.gguf" or "hf:owner/repo::file.gguf"
    """
    p = Path(identifier)
    if p.exists():
        return str(p)

    repo_id = None
    filename_hint = None
    working_id = identifier
    if "::" in identifier:
        working_id, filename_hint = identifier.split("::", 1)

    if working_id.startswith("hf:"):
        repo_id = working_id.split("hf:", 1)[1]
    elif "/" in working_id and not working_id.endswith(".gguf"):
        repo_id = working_id

    if repo_id is None:
        return identifier

    try:
        from huggingface_hub import snapshot_download
    except Exception:
        print("huggingface_hub not installed; cannot auto-download models. Provide a local path instead.")
        return identifier

    hf_token = os.environ.get("HUGGINGFACE_HUB_TOKEN") or os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
    try:
        cache_dir = snapshot_download(repo_id=repo_id, repo_type="model", token=hf_token, force_download=force_download)
    except Exception as e:
        print(f"Failed to download from Hugging Face: {e}")
        return identifier

    # If caller specified exact filename, prefer it
    if filename_hint:
        cand = Path(cache_dir) / filename_hint
        if cand.exists():
            return str(cand)

    ggufs = list(Path(cache_dir).rglob("*.gguf"))
    if ggufs:
        return str(ggufs[0])

    # fallback to other model file extensions
    for ext in ("*.bin", "*.safetensors"):
        found = list(Path(cache_dir).rglob(ext))
        if found:
            return str(found[0])

    return identifier


def _extract_text_from_llama(obj) -> str:
    """Extract text from various llama-cpp-python response shapes."""
    if obj is None:
        return ""
    if isinstance(obj, str):
        return obj
    if isinstance(obj, (bytes, bytearray)):
        try:
            return obj.decode("utf-8", errors="ignore")
        except Exception:
            return str(obj)
    if isinstance(obj, dict):
        if "text" in obj and isinstance(obj.get("text"), str):
            return obj.get("text", "")
        choices = obj.get("choices")
        if isinstance(choices, (list, tuple)) and choices:
            first = choices[0]
            if isinstance(first, dict) and "text" in first:
                return first.get("text", "")
        delta = obj.get("delta")
        if isinstance(delta, dict):
            return delta.get("content") or delta.get("text") or ""
    try:
        return str(obj)
    except Exception:
        return ""


class YOLOWorldDetector:
    def __init__(self, model_path: str):
        print(f"Loading YOLO-World model from {model_path}...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = YOLO(model_path)
        try:
            self.model.set_classes(["person", "door", "table"])
        except Exception:
            pass

    def detect(self, image_path: str, conf_threshold: float = 0.1):
        image = Image.open(image_path).convert("RGB")
        start = time.time()
        results = self.model(image, conf=conf_threshold, verbose=False)
        inference_time = time.time() - start
        detections = []
        for r in results:
            for box in getattr(r, "boxes", []):
                try:
                    class_id = int(box.cls[0])
                    class_name = self.model.names.get(class_id, str(class_id))
                    conf = float(box.conf[0])
                    xyxy = box.xyxy[0].cpu().numpy()
                    detections.append({"class": class_name, "confidence": conf, "bbox": [float(v) for v in xyxy]})
                except Exception:
                    continue
        return {"inference_time": inference_time, "detections": detections}


def run_yolo_latency_test(image_path: str, model_path: str, num_runs: int = 50):
    print("="*60)
    print("YOLO-WORLD LATENCY TEST")
    print("="*60)

    if not Path(model_path).exists():
        print(f"YOLO Model not found at: {model_path}. Skipping test.")
        return None
    if not Path(image_path).exists():
        print(f"Test image not found at: {image_path}. Skipping YOLO test.")
        return None

    detector = YOLOWorldDetector(model_path=model_path)
    # warmup
    _ = detector.detect(image_path)

    timings = []
    for _ in range(num_runs):
        res = detector.detect(image_path)
        timings.append(res["inference_time"])

    avg = sum(timings) / len(timings)
    return {Path(model_path).name: {"average_latency": avg, "fps": (1/avg if avg>0 else 0)}}


def run_llm_latency_test(model_path: str, num_runs: int = 1, max_tokens: int = 500):
    """Simple streaming-first LLM latency test.

    Streams tokens (prints as they arrive). Falls back to a single non-streaming attempt if streaming raises.
    """
    print("\n" + "="*60)
    print("LLM LATENCY TEST")
    print("="*60)

    if Llama is None:
        print("llama-cpp-python not installed; skipping LLM tests.")
        return None

    resolved = resolve_llm_model_path(model_path)
    model_name = Path(resolved).name
    if not Path(resolved).exists():
        print(f"Model not found at {resolved}; skipping.")
        return {model_name: "not found"}
    temperature = 0
    print(f"Loading LLM {model_name}...")
    llm = Llama(model_path=resolved, verbose=False, n_gpu_layers=0, temperature=temperature)
    print("Model loaded.")

    # Strict instruction + sentinel token so we can reliably detect the end.
    user_prompt = (
        "List 20 everyday objects a YOLO-world model might mistake for a 'black computer mouse'. Do not repeat any item in the list. "
        "Output ONLY a comma-separated list with no explanation and terminate the list immediately after."
    )
    if model_name.lower().startswith("qwen"):
        prompt = (f"<|im_start|>user\n{user_prompt}<|im_end|>\n<|im_start|>assistant\n<think>Make the list</think>\n")
        stop=["<|im_end|>", "<|endoftext|>"]
    else:
        if model_name.lower().startswith("llama"):
            prompt = (
                f"<|start_header_id|>user<|end_header_id|>\n\n{user_prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
            )
            stop=["<|eot_id|>", "<|end_of_text|>"]
        else:
            return -1

    # quick warmup (non-stream) with deterministic sampling and stop
    try:
        _ = llm(prompt, max_tokens=1, stream=False, temperature=temperature, stop=stop)
    except Exception:
        pass

    timings = {"ttft": [], "total": [], "tps": []}

    for i in range(num_runs):
        print(f"Run {i+1}/{num_runs}...", end=" ", flush=True)
        start = time.time()
        first_time = None
        out_text = ""
        try:
            # stream with deterministic sampling and stop tokens
            for chunk in llm(prompt, max_tokens=max_tokens, stream=True, temperature=temperature, stop=stop):
                txt = _extract_text_from_llama(chunk)
                if txt:
                    if first_time is None:
                        first_time = time.time()
                    print(txt, end="", flush=True)
                    out_text += txt
            print()
            end = time.time()
            total = end - start
            ttft = (first_time - start) if first_time else total
            toks = len(out_text.split()) if out_text else 0
            tps = toks / total if total>0 else 0
        except Exception as e:
            print(f"\n[stream failed] falling back to non-stream: {e}")
            s = time.time()
            res = llm(prompt, max_tokens=max_tokens, stream=False, temperature=temperature, stop=stop)
            e2 = time.time()
            total = e2 - s
            out_text = _extract_text_from_llama(res) if isinstance(res, dict) else str(res)
            print(out_text)
            ttft = total
            toks = len(out_text.split()) if out_text else 0
            tps = toks / total if total>0 else 0
        # Truncate at sentinel if present; otherwise trim to first line or 60 words
        if "<END>" in out_text:
            out_text = out_text.split("<END>", 1)[0].strip()
        else:
            # prefer first line if model kept explaining
            if "\n" in out_text:
                out_text = out_text.split("\n", 1)[0].strip()
            # final safety: limit to 60 words
            words = out_text.split()
            if len(words) > 60:
                out_text = " ".join(words[:60]).strip()

        timings["ttft"].append(ttft)
        timings["total"].append(total)
        timings["tps"].append(tps)

        print(f"TTFT: {ttft:.3f}s, Total: {total:.3f}s, TPS: {tps:.2f}")

    return {model_name: {"average_ttft": sum(timings["ttft"]) / len(timings["ttft"]),
                         "average_total": sum(timings["total"]) / len(timings["total"]),
                         "average_tps": sum(timings["tps"]) / len(timings["tps"])}}


if __name__ == "__main__":
    # Construct absolute paths based on script location
    YOLO_MODEL_PATH = str(Path(__file__).parent.parent.parent / "perception" / "yolov8s-world.pt")
    TEST_IMAGE_PATH = str(Path(__file__).parent / "test_images" / "test.jpeg")
    YOLO_RUNS = 10
    LLM_RUNS = 1

    LLM_MODELS = {
        "Qwen-0.6B": "unsloth/Qwen3-0.6B-GGUF::Qwen3-0.6B-BF16.gguf",
        "Llama-1B-Instruct": "hf:unsloth/Llama-3.2-1B-Instruct-GGUF",
    }

    results = {}

    y = run_yolo_latency_test(TEST_IMAGE_PATH, YOLO_MODEL_PATH, num_runs=YOLO_RUNS)
    if y:
        results['yolo_world'] = y

    if Llama:
        llm_res = {}
        for name, path in LLM_MODELS.items():
            r = run_llm_latency_test(path, num_runs=LLM_RUNS)
            if r:
                llm_res.update(r)
        if llm_res:
            results['llms'] = llm_res

    if results:
        with open('latency_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print('\nResults saved to latency_results.json')
    else:
        print('\nNo tests were run successfully.')
