import ollama
from pydantic import BaseModel, Field
from typing import List

# 1. Define the Schema for the confused objects
class ConfusedObject(BaseModel):
    name: str = Field(description="Strictly 1 word. Use general object classes (e.g., 'Remote' instead of 'TV Remote'). Do not repeat back the original item.")

class ConfusionList(BaseModel):
    items: List[ConfusedObject]

# 2. Define the target object
target_objects = ["xbox controller", "desk lamp", "black breakfast bar", "red backpack", "notebook", "book", "door"]

# 3. Create the precedent (Few-Shot Examples)
base_messages = [
    {
        'role': 'system', 
        'content': 'You are a visual recognition expert. List 4 everyday items that could be visually confused for the target object. Provide general class names (nouns) rather than specific descriptions. Do not repeat items.'
    },
    # Precedent 1: Coffee Mug
    # User input remains specific, Assistant output becomes general classes
    {'role': 'user', 'content': 'target: red coffee mug'},
    {'role': 'assistant', 'content': '{"items": [{"name": "Container"}, {"name": "Pot"}, {"name": "Cup"}, {"name": "Pitcher"}]}'},
    
    # Precedent 2: Smartphone
    {'role': 'user', 'content': 'target: black smartphone'},
    {'role': 'assistant', 'content': '{"items": [{"name": "Remote"}, {"name": "Calculator"}, {"name": "Battery"}, {"name": "Wallet"}]}'},

    # Precedent 3: Laptop
    {'role': 'user', 'content': 'target: silver laptop'},
    {'role': 'assistant', 'content': '{"items": [{"name": "Computer"}, {"name": "Monitor"}, {"name": "Box"}, {"name": "Binder"}]}'},
    
    # Precedent 4: Water Bottle
    {'role': 'user', 'content': 'target: metal water bottle'},
    {'role': 'assistant', 'content': '{"items": [{"name": "Flashlight"}, {"name": "Canister"}, {"name": "Thermos"}, {"name": "Pipe"}]}'},

    # Precedent 5 (NEW): Computer Mouse
    {'role': 'user', 'content': 'target: wireless computer mouse'},
    {'role': 'assistant', 'content': '{"items": [{"name": "Remote"}, {"name": "Shoe"}, {"name": "Powerbank"}, {"name": "Toy"}]}'},

    # Precedent 6 (NEW): Sunglasses
    {'role': 'user', 'content': 'target: black sunglasses'},
    {'role': 'assistant', 'content': '{"items": [{"name": "Goggles"}, {"name": "Headphones"}, {"name": "Mask"}, {"name": "Binoculars"}]}'},

]

for target_object in target_objects:
    messages = base_messages + [{'role': 'user', 'content': f'target: {target_object}'}]

    # 4. Run the model (Gemma 3 1B)
    response = ollama.chat(
        model='gemma3:1b', # Ensure you have this model pulled
        messages=messages,
        format=ConfusionList.model_json_schema(),
        options={'temperature': 0} # Slightly above 0 allows a tiny bit of creativity while adhering to format
    )

    # 5. Parse and Print
    try:
        data = ConfusionList.model_validate_json(response.message.content)
        print(f"--- Objects likely confused with: {target_object} ---")
        for i, item in enumerate(data.items, 1):
            print(f"{i}. {item.name.upper()}")
    except Exception as e:
        print(f"Error: {e}")
        print(f"Raw Output: {response.message.content}")