import json
from pathlib import Path
from pydantic import BaseModel, Field
from llama_cpp import Llama

# --- This is the object that the function returns, see field descriptions ---
class ObjectExtraction(BaseModel):
    object_of_interest: str = Field(description="A description containing exactly 1 to 4 words.")
    status: str = Field(description="Either 'success' or 'failure' depending on whether a reasonable object was extracted.") # Failure means the input was rejected by the model. It does not mean that the model responded with an error.

# --- Model singleton ---
_llm: Llama | None = None

# Default GGUF path: project_root/gemma3-vosk-q4.gguf
_DEFAULT_GGUF = Path(__file__).resolve().parent.parent / "gemma3-vosk-q4.gguf"

# System prompt (from Modelfile)
_SYSTEM = (
    "You are a minimalist entity extractor. "
    "If there is a reasonable object in the input, extract ONLY the object name. "
    "Your response MUST be 1, 2, 3, or 4 words long maximum. "
    "If there is no object, respond with status failure. "
    "Do not include any punctuation."
)

# GBNF grammar to guarantee valid JSON matching ObjectExtraction schema
_JSON_GRAMMAR = r'''
root   ::= "{" ws "\"object_of_interest\"" ws ":" ws string "," ws "\"status\"" ws ":" ws status ws "}"
string ::= "\"" chars "\""
chars  ::= char*
char   ::= [^"\\] | "\\" escape
escape ::= ["\\nrt/]
status ::= "\"success\"" | "\"failure\""
ws     ::= [ \t\n]*
'''

def _build_prompt(text: str) -> str:
    """Build a Gemma-3 chat prompt with system instruction and few-shot examples."""
    return (
        f"<start_of_turn>user\n{_SYSTEM} where is the the the red hammer<end_of_turn>\n"
        f"<start_of_turn>model\n"
        f'{{"object_of_interest": "red hammer", "status": "success"}}<end_of_turn>\n'
        f"<start_of_turn>user\n{_SYSTEM} go to the place for it<end_of_turn>\n"
        f"<start_of_turn>model\n"
        f'{{"object_of_interest": "N/A", "status": "failure"}}<end_of_turn>\n'
        f"<start_of_turn>user\n{_SYSTEM} {text}<end_of_turn>\n"
        f"<start_of_turn>model\n"
    )

# --- The Core Function ---
def get_extracted_object(text: str) -> ObjectExtraction:
    """
    Takes raw text, processes it via the fine-tuned Gemma-3 model,
    and returns a structured ObjectExtraction object.
    """
    global _llm
    if _llm is None:
        load_extractor_model()

    try:
        prompt = _build_prompt(text)
        output = _llm(
            prompt,
            max_tokens=64,
            temperature=0,
            stop=["<start_of_turn>", "<end_of_turn>"],
            grammar=_grammar,
        )
        raw = output["choices"][0]["text"].strip()
        return ObjectExtraction.model_validate_json(raw)

    except Exception as e:
        print(f"Extraction Error: {e}")
        return ObjectExtraction(object_of_interest="N/A", status="failure")

# Compiled grammar object (created on first load)
_grammar = None

def load_extractor_model(model_path: str | None = None):
    """
    Loads the Gemma-3 GGUF model into memory.
    Call this function at the start of your application.
    No external server (Ollama) required.
    """
    global _llm, _grammar
    from llama_cpp import LlamaGrammar

    gguf = Path(model_path) if model_path else _DEFAULT_GGUF
    try:
        print(f"Loading extraction model from {gguf} ...")
        _llm = Llama(
            model_path=str(gguf),
            n_gpu_layers=0,   # CPU-only on Pi
            n_ctx=256,        # small context is enough for this task
            verbose=False,
        )
        _grammar = LlamaGrammar.from_string(_JSON_GRAMMAR)
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Model Load Error: {e}")
        _llm = None

# --- Simple Test ---
if __name__ == "__main__":
    test_input = "find the the red hammer on the bench"
    result = get_extracted_object(test_input)

    print(f"Input: {test_input}")
    print(f"Object: {result.object_of_interest}")
    print(f"Status: {result.status}")