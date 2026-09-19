## Import the necessary modules
import json
import os
from parse_data import load_items, get_unclaimed_items, save_result

## Import the function from the module parse_data
# (Already imported above)

## Build your prompt based on the description the user provides 
## and the items that are available in the lost-and-found database.
## The model must follow the rules listed in the README file
## The function should return the system prompt and the user prompt.
## You may need to use json.dumps() to convert the available_items list into a JSON string.

def build_prompt(description, available_items):
    system_prompt = (
        "You are a campus lost-and-found assistant. Your task is to find possible matches "
        "for a lost item based on a user's description and a provided list of available items.\n\n"
        "Rules:\n"
        "1. Use ONLY the given JSON file.\n"
        "2. Not all details of an item must match to be a possible match.\n"
        "3. Return ONLY JSON with exactly this structure: {\"matches\": [\"ITEM_ID\"], \"confidence\": \"LOW\"}\n"
        "4. \"matches\" contains all the possible matches.\n"
        "5. \"confidence\" must be exactly one of: LOW, MEDIUM, HIGH.\n"
        "6. If there is no match, return an empty list for matches."
    )
    
    items_json = json.dumps(available_items, indent=2)
    user_prompt = f"User description: {description}\n\nAvailable items:\n{items_json}"
    
    return system_prompt, user_prompt
    

## Logic to ask Qwen for all the possible matches based on the system prompt and user prompt.
## The function should return the response from Qwen.
def ask_qwen(system_prompt, user_prompt):
    import ollama
    response = ollama.chat(model='qwen2.5:7b', messages=[
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': user_prompt},
    ])
    return response['message']['content']


## Logic to parse the response from Qwen and return the result. 
## You may need to use json.loads() to convert the response string into a suitable Python data structure.
def parse_response(response_text):
    # Clean up potential markdown code blocks
    text = response_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None
    


## Logic to validate the result returned by Qwen.
## It should check if the result is a dictionary, contains the keys "matches" and "confidence", and that the values are of the correct type.
## If everything is correct, then it should check if the item IDs in the "matches" list are valid IDs .
def validate_result(result, available_items):
    if not isinstance(result, dict):
        return False
    if "matches" not in result or "confidence" not in result:
        return False
    if not isinstance(result["matches"], list):
        return False
    if result["confidence"] not in ["LOW", "MEDIUM", "HIGH"]:
        return False
    
    valid_ids = {item["id"] for item in available_items}
    for match_id in result["matches"]:
        if match_id not in valid_ids:
            return False
            
    return True


## Logic to display the matches found by Qwen in a user-friendly format.
## If no matches are found, it should display a message indicating that no matches were found, along with the empty list
def display_matches(result, available_items):
    print("\nMATCH RESULT")
    print("-" * 50)
    print(f"Confidence: {result['confidence']}")
    
    if not result["matches"]:
        print("\nNo matches found.")
        print("Possible matches: []")
        return

    print("\nPossible matches:\n")
    item_map = {item["id"]: item for item in available_items}
    
    for match_id in result["matches"]:
        item = item_map.get(match_id)
        if item:
            print(f"ID: {item['id']}")
            print(f"Item: {item['item']}")
            print(f"Color: {item['color']}")
            print(f"Location: {item['location']}")
            print(f"Date found: {item['date']}\n")


## Control center for the entire program.
def main():
    print("CAMPUS LOST-AND-FOUND ASSISTANT")
    print("=" * 50)
    
    description = input("Describe the item you lost: ")
    print("\nSearching for possible matches...\n")
    
    # Load and filter items
    all_items = load_items("found_items.json")
    available_items = get_unclaimed_items(all_items)
    
    # Build prompt and ask Qwen
    system_prompt, user_prompt = build_prompt(description, available_items)
    response_text = ask_qwen(system_prompt, user_prompt)
    
    # Parse and validate
    result = parse_response(response_text)
    
    if result is None:
        print("Error: Could not parse the model's response.")
        return
        
    if not validate_result(result, available_items):
        print("Error: The model's response did not pass validation.")
        print(f"Raw response: {response_text}")
        return
    
    # Display and save
    display_matches(result, available_items)
    
    output_filename = "output/match_result.json"
    save_result(result, output_filename)
    print(f"Result saved to {output_filename}")


if __name__ == "__main__":
    main()
