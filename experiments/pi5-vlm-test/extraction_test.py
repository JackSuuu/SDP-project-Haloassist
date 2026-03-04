import ollama
from pydantic import BaseModel, Field

class ObjectExtraction(BaseModel):
    # The description helps guide the LLM's internal attention
    object_of_interest: str = Field(description="A description containing exactly 1 to 4 words.")

user_input = "find me a bannana but make sure its ripe"

response = ollama.chat(
    model='gemma3:1b',
    messages=[
        {
            'role': 'system', 
            'content': 'You are a minimalist entity extractor. Extract ONLY the object name. Your response MUST be 1, 2, 3, or 4 words long maximum. Never exceed 4 words.'
        },
        # Few-shot examples specifically modeling the 4-word limit
        {'role': 'user', 'content': 'i need the big blue water bottle on the desk'},
        {'role': 'assistant', 'content': '{"object_of_interest": "big blue water bottle"}'}, # 4 words
        
        {'role': 'user', 'content': 'where is that laptop'},
        {'role': 'assistant', 'content': '{"object_of_interest": "laptop"}'}, # 1 word
        
        {'role': 'user', 'content': 'pick up the small metal wrench'},
        {'role': 'assistant', 'content': '{"object_of_interest": "small metal wrench"}'}, # 3 words
        
        # Actual Task
        {'role': 'user', 'content': user_input}
    ],
    format=ObjectExtraction.model_json_schema(),
    options={'temperature': 0}
)

try:
    data = ObjectExtraction.model_validate_json(response.message.content)
    # Final check: Clean up any accidental extra words via Python
    final_text = " ".join(data.object_of_interest.split()[:4])
    print(f"Extracted: {final_text}")
except Exception as e:
    print(f"Failed: {e}")