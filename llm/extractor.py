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
            messages=[
                {'role': 'user', 'content': 'where about did the large yellow pickaxe go'},
                {'role': 'assistant', 'content': '{"object_of_interest": "large yellow pickaxe", "status": "success"}'},
                {'role': 'user', 'content': text}
            ],
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
    "where exactly did the screwdriver go", "locate the black leather wallet in my backpack", "government id", "the wallet", "where are my car keys"
]
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
    for test_input in requests + nonsense_requests:
        result = get_extracted_object(test_input)
        if result.status == "success" and result.object_of_interest.strip().lower() != "n/a" and result.object_of_interest.strip() != "large yellow pickaxe":
            print("✅ Valid Object Extracted")
        else:
            print("❌ Invalid Object Extracted")
        print(f"Input: {test_input}")
        print(f"Object: {result.object_of_interest}")
        print(f"Status: {result.status}")