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
        f"<start_of_turn>user\n{_SYSTEM} i cannot find where about did the large yellow pickaxe go<end_of_turn>\n"
        f"<start_of_turn>model\n"
        f'{{"object_of_interest": "large yellow pickaxe", "status": "success"}}<end_of_turn>\n'
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
            n_ctx=512,        # small context is enough for this task
            verbose=False,
        )
        _grammar = LlamaGrammar.from_string(_JSON_GRAMMAR)
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Model Load Error: {e}")
        _llm = None

# --- Simple Test ---
if __name__ == "__main__":
    requests = [
    "please tell me the location of the television remote",
    "have you seen my blue denim jacket anywhere", "locate the nearest pair of scissors for me",
    "i am looking for the charging cable for my phone", "point me toward the umbrella stand",
    "can you find where the spare batteries are kept", "find my reading glasses on the coffee table",
    "the kitchen timer seems to have vanished", "search for the bottle opener in the top drawer",
    "identify the current spot of the dog leash", "do you know where the extra paper towels are stored",
    "help me track down my reusable water bottle", "i cannot find the stapler on my desk",
    "where is the box of tissues hidden", "spot the laundry detergent near the washing machine",
    "the flashlight should be in the hallway closet", "trace the location of my silver watch",
    "is the salt shaker still on the dining table", "check if the mail is on the entryway bench",
    "reveal the hiding place of the spare house key", "look for the hammer in the toolbox",
    "my sunglasses are missing from the dashboard", "where might the rolls of scotch tape be",
    "detect the position of the oven mitts", "find the digital thermometer in the medicine cabinet",
    "tell me where the light bulbs are located", "i need to find the yoga mat in the gym bag",
    "where exactly did the screwdriver go", "locate the black leather wallet in my backpack", "government id", "the wallet", "where are my car keys"]
    nonsense_requests = [
    "where is the fast of the blue",
    "can you locate the very quickly",
    "please find the under of the over",
    "i am looking for the purple of the yesterday",
    "point me toward the loud of the soft",
    "where did i leave the why",
    "help find between of the nowhere",
    "search for the almost near the almost",
    "tell me the location of the because",
    "locate extremely within the suddenly"
    ]
    for req in requests + nonsense_requests:
        test_input = req
        result = get_extracted_object(test_input)

        print(f"Input: {test_input}")
        print(f"Object: {result.object_of_interest}")
        print(f"Status: {result.status}")
