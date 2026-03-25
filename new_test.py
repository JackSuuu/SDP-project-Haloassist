import os
# Force basic CPU/GPU settings before loading Llama to prevent Windows/3.13 crashes
os.environ["GGML_CUDA_NO_PINNED"] = "1" 

import json
from pathlib import Path
from pydantic import BaseModel, Field
from llama_cpp import Llama

class ObjectExtraction(BaseModel):
    object: str = Field(description="A description containing exactly 1 to 4 words. 'N/A' if none.")
    status: bool = Field(description="True if a reasonable object was extracted, False otherwise.")

_llm: Llama | None = None
_DEFAULT_GGUF = Path(r"D:\University\Year3\Sem2\SDP\Project\SDP-project-Haloassist\experiments\pi5-vlm-test\functiongemma-270M-vosk-extractor-Q8_0-LoRA.gguf")
_SYSTEM = "Parse object, 4 words max"

_JSON_GRAMMAR = r'''
root   ::= "{" ws "\"object\"" ws ":" ws string "," ws "\"status\"" ws ":" ws boolean ws "}"
string ::= "\"" chars "\""
chars  ::= char*
char   ::= [^"\\] | "\\" escape
escape ::= ["\\nrt/]
boolean::= "true" | "false"
ws     ::= [ \t\n]*
'''

def _build_prompt(text: str) -> str:
    return f"<start_of_turn>user\n{_SYSTEM}\n\n{text}<end_of_turn>\n<start_of_turn>model\n"

def get_extracted_object(text: str) -> ObjectExtraction:
    global _llm
    if _llm is None: load_extractor_model()
    try:
        output = _llm(_build_prompt(text), max_tokens=32, temperature=0.0, 
                      stop=["<end_of_turn>", "<eos>"], grammar=_grammar)
        raw = output["choices"][0]["text"].strip()
        return ObjectExtraction.model_validate_json(raw)
    except Exception as e:
        return ObjectExtraction(object="N/A", status=False)

_grammar = None

def load_extractor_model(model_path: str | None = None):
    global _llm, _grammar
    from llama_cpp import LlamaGrammar
    gguf = Path(model_path) if model_path else _DEFAULT_GGUF
    try:
        _llm = Llama(model_path=str(gguf), n_gpu_layers=-1, n_ctx=256, n_threads=4, verbose=False)
        _grammar = LlamaGrammar.from_string(_JSON_GRAMMAR)
        print(f"✅ Model Loaded: {gguf.name}\n")
    except Exception as e:
        print(f"❌ Load Error: {e}")

if __name__ == "__main__":
    test_suite = {
        "Grammar Decay (Missing Verbs/Articles)": [
            "blue bottle desk",                  # Just nouns/adjectives
            "find small red cup kitchen",        # Missing 'the' and 'in the'
            "where black phone is",              # Yoda-style word order
            "need yellow hammer now",            # Missing subject/article
            "search keys coffee table"           # Missing prepositions
        ],
        "Interjected Fillers (Stuttering/Hesitation)": [
            "find the uh blue water bottle",     # Single interjection
            "where is the um like green plant",  # Multiple fillers
            "can you get the you know watch",    # Phrase interjection
            "find me the actually the phone",    # Mid-sentence correction
            "the uh tablet where is it"          # Disjointed structure
        ],
        "Word Order & Reversal": [
            "bottle water blue find me",         # Reverse order
            "on the table the remote is",        # Prepositional start
            "glasses reading search for",        # Noun-first
            "the big television find that",      # Noun-object focus
            "charger phone i need"               # Object-subject-verb
        ],
        "Strict Negatives (No valid object)": [
            "the thing is the thing",            # Circular, no object
            "where did it go",                   # Pronoun only
            "find the because of the",           # Prepositional soup
            "is the is the is the",              # Repetition only
            "tell me why the how"                # Question words only
        ],
        "Multi-Adjective Stress": [
            "find large heavy metal bowl",       # 4 words exactly
            "the small round white plastic cap", # Too many adjectives (check 4-word limit)
            "where is my old dirty work boot",   # Adjective heavy
            "grab that one single gold coin"     # Numerical/Specific
        ]
    
    }
    
    for category, cases in test_suite.items():
        print(f"=== CATEGORY: {category} ===")
        for req in cases:
            result = get_extracted_object(req)
            status_icon = "✅" if result.status else "❌"
            print(f"[{status_icon}] In: {req}")
            print(f"     Out: {result.object} ({result.status})\n")
        print()