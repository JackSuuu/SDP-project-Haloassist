import ollama
from pydantic import BaseModel, Field

# --- This is the object that the function returns, see field descriptions ---
class ObjectExtraction(BaseModel):
    object_of_interest: str = Field(description="A description containing exactly 1 to 4 words.")
    status: str = Field(description="Either 'success' or 'failure' depending on whether a reasonable object was extracted.") # Failure means the input was rejected by the model. It does not mean that the model responded with an error.

# --- The Core Function ---
def get_extracted_object(text: str) -> ObjectExtraction:
    """
    Takes raw text, processes it via the fine-tuned Gemma-3 model,
    and returns a structured ObjectExtraction object.
    """
    try:
        response = ollama.chat(
            model='gemma3-vosk-q4',
            messages=[{'role': 'user', 'content': text}],
            format=ObjectExtraction.model_json_schema(),
            options={'temperature': 0}
        )
        
        # Parse the JSON response into our Pydantic model
        return ObjectExtraction.model_validate_json(response.message.content)

    except Exception as e:
        print(f"Extraction Error: {e}")
        # Return a fallback failure object if the LLM or network fails
        return ObjectExtraction(object_of_interest="N/A", status="failure")
    
def load_extractor_model():
    """
    Preloads the Gemma-3 model to reduce latency on the first call.
    Call this function at the start of your application.
    """
    try:
        print("Preloading object extraction model...")
        ollama.generate(
            model='gemma3-vosk-q4',
            prompt="",
            keep_alive='1h' # Keep the model loaded for 1 hour (adjust as needed)
        )
        print("Model preloaded successfully.")
    except Exception as e:
        print(f"Model Preload Error: {e}")

# --- Simple Test ---
if __name__ == "__main__":
    test_input = "find the the red hammer on the bench"
    result = get_extracted_object(test_input)
    
    print(f"Input: {test_input}")
    print(f"Object: {result.object_of_interest}")
    print(f"Status: {result.status}")