import google.generativeai as genai
import os
import json # For attempting to parse the AI's JSON response

# It's good practice to load the API key from environment variables in a real app
# For this example, it's passed as an argument.

def get_ai_analysis(api_key: str, grocery_list: str, brochure_content: str) -> dict:
    """
    Analyzes brochure content to extract all product offers using Google Gemini API.
    The grocery_list parameter is currently not used in the prompt for this function,
    as the focus is on extracting all offers from the brochure.

    Args:
        api_key: The Google Gemini API key.
        grocery_list: A string containing the user's grocery list (currently unused by the prompt).
        brochure_content: A string containing the text content of the grocery brochure.

    Returns:
        A dictionary containing the AI's response (ideally a JSON string of offers)
        or an error message.
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name='gemini-pro')

        prompt = f"""
        You are a specialized data extraction assistant. Your task is to scan the provided grocery brochure content
        and identify all distinct product offers. For each offer, extract the following details:
        - product_name: The name of the product as it appears in the brochure.
        - price: The price of the product (e.g., "2.99", "1.45", "0.89").
        - unit: The unit associated with the price (e.g., "kg", "Stück", "Packung", "Liter", "g", "ml", "Bund", "Netz", "Schale"). If the price is per item or pack, common units are "Stück" or "Packung". If no unit is explicitly mentioned but implied (e.g. for a single item like a bottle of soda), use "Stück".
        - offer_condition: Any special conditions or notes related to the offer, such as "Kaufe 2, zahle 1", "Ab 3 Packungen X€", "pro 100g", "nur gültig am [Datum/Tag]", "solange der Vorrat reicht". If no special condition is mentioned, use null or an empty string.

        The brochure content is as follows:
        --- BROCHURE CONTENT START ---
        {brochure_content}
        --- BROCHURE CONTENT END ---

        Return your findings as a single JSON array of objects. Each object in the array should represent one product offer.
        Do NOT include any text or explanations outside of the JSON array itself.

        Example of the desired JSON output format:
        [
          {{
            "product_name": "Rispentomaten",
            "price": "1.99",
            "unit": "kg",
            "offer_condition": null
          }},
          {{
            "product_name": "Frische Vollmilch 3.5%",
            "price": "0.95",
            "unit": "Liter",
            "offer_condition": "Beim Kauf von 2 Stück nur 1.80€"
          }}
        ]
        
        Ensure the output is a valid JSON array.
        """
        
        response = model.generate_content(prompt)
        
        ai_response_text = None
        if hasattr(response, 'text') and response.text:
            ai_response_text = response.text
        elif response.parts:
            ai_response_text = "".join(part.text for part in response.parts if hasattr(part, 'text'))
        
        if ai_response_text:
            if ai_response_text.strip().startswith("```json"):
                ai_response_text = ai_response_text.strip()[7:]
                if ai_response_text.strip().endswith("```"):
                    ai_response_text = ai_response_text.strip()[:-3]
            try:
                json.loads(ai_response_text) 
                return {"status": "success", "ai_response": ai_response_text}
            except json.JSONDecodeError as je:
                return {
                    "status": "error", 
                    "message": "AI response from offer extraction was not valid JSON.", 
                    "ai_raw_response": ai_response_text,
                    "details": str(je)
                }
        else:
            feedback = str(response.prompt_feedback) if hasattr(response, 'prompt_feedback') else "No feedback available."
            if response.candidates and response.candidates[0].finish_reason.name != "STOP":
                 feedback += f" Finish Reason: {response.candidates[0].finish_reason.name}"
            return {"status": "error", "message": "AI offer extraction response format not recognized or empty.", "details": feedback}

    except ValueError as ve:
        return {"status": "error", "message": f"API Key configuration error during offer extraction: {str(ve)}"}
    except Exception as e:
        error_message = f"An unexpected error occurred with the AI service during offer extraction: {str(e)}"
        if hasattr(e, 'message'): 
             error_message = f"AI service error (offer extraction): {e.message}"
        return {"status": "error", "message": error_message}


def match_item_to_brochure_offers(api_key: str, user_item: str, extracted_offers: list[dict]) -> dict | None:
    """
    Matches a single user grocery item against a list of extracted brochure offers using semantic search with Gemini.

    Args:
        api_key: The Google Gemini API key.
        user_item: The grocery item string from the user's list (e.g., "Tomaten").
        extracted_offers: A list of offer dictionaries (previously extracted by get_ai_analysis).
                          Example: [{"product_name": "Bio Rispentomaten", "price": "2.49", ...}, ...]

    Returns:
        The full dictionary of the best matched offer from extracted_offers if a good match is found.
        Returns None if no satisfactory match is found or an error occurs.
    """
    if not extracted_offers:
        return None # No offers to match against

    try:
        genai.configure(api_key=api_key) # Ensure API key is configured for this call too
        model = genai.GenerativeModel('gemini-pro')

        # Create a simplified list of product names from the brochure for the prompt
        brochure_product_names = [offer.get("product_name", "Unknown Product") for offer in extracted_offers]
        
        prompt = f"""
        You are a semantic matching assistant. Your task is to find the best match for a user's grocery item
        from a list of product names extracted from a grocery brochure.

        User's grocery item: "{user_item}"

        List of product names from the brochure:
        {json.dumps(brochure_product_names, ensure_ascii=False)}

        Instructions:
        1. Analyze the user's grocery item.
        2. Compare it semantically against each product name in the provided list from the brochure.
        3. Identify the single best match from the brochure list. The match should be a close semantic equivalent. For example, "Tomaten" should match "Bio Rispentomaten". "Milch" should match "Frische Vollmilch 3.5%".
        4. If a good semantic match is found, respond with ONLY the exact product name from the brochure list that is the best match. For example, if "Bio Rispentomaten" is the best match for "Tomaten", respond with "Bio Rispentomaten".
        5. If multiple items could match, pick the most general or common one, or the one that seems like the best deal if price information were available (though it is not provided in this step, so focus on name similarity).
        6. If no product name from the brochure list is a good semantic match for the user's item, respond with the exact string "NO_MATCH_FOUND".

        Do not include any explanations or other text in your response. Only the matched product name or "NO_MATCH_FOUND".

        Example Response for a match:
        Bio Rispentomaten

        Example Response for no match:
        NO_MATCH_FOUND
        """

        response = model.generate_content(prompt)
        
        matched_product_name = None
        if hasattr(response, 'text') and response.text:
            matched_product_name = response.text.strip()
        elif response.parts:
            matched_product_name = "".join(part.text for part in response.parts if hasattr(part, 'text')).strip()

        if matched_product_name and matched_product_name != "NO_MATCH_FOUND":
            # Find the full offer dictionary corresponding to the matched product name
            for offer in extracted_offers:
                if offer.get("product_name") == matched_product_name:
                    return offer # Return the full offer dictionary
            # This case should ideally not happen if AI returns a name from the list, but as a fallback:
            return {"status": "error", "message": "AI matched a name not in the provided offer list.", "matched_name": matched_product_name}
        elif matched_product_name == "NO_MATCH_FOUND":
            return None # Explicit no match
        else:
            # Handle cases where AI response is unexpected (e.g., empty or malformed)
            # print(f"Unexpected AI response for item '{user_item}': '{matched_product_name}'") # For server logging
            return None 

    except ValueError as ve: # Handles API key configuration errors
        # print(f"API Key error during matching for '{user_item}': {str(ve)}") # Server logging
        return {"status": "error", "message": f"API Key configuration error during matching: {str(ve)}"} # Indicate error
    except Exception as e:
        # print(f"Error matching item '{user_item}': {str(e)}") # Server logging
        error_message = f"Error matching item '{user_item}': {str(e)}"
        if hasattr(e, 'message'):
             error_message = f"AI service error (matching item '{user_item}'): {e.message}"
        return {"status": "error", "message": error_message}


if __name__ == '__main__':
    print("Running direct tests of ai_client.py...")
    test_api_key = os.environ.get("GOOGLE_API_KEY")

    if not test_api_key:
        print("Please set the GOOGLE_API_KEY environment variable to run this test.")
        print("Example: export GOOGLE_API_KEY='your_api_key_here'")
    else:
        print(f"Using API Key: {'*' * (len(test_api_key) - 4) + test_api_key[-4:]}")
        
        # Sample brochure content (text extracted from a PDF)
        sample_brochure_text = """
        ALDI WOCHENEND-HIGHLIGHTS AB FR. 31.5.
        Frischeparadies!
        Bio-Speisekartoffeln Sorte: siehe Etikett, Deutschland, Kl. II 2,5-kg-Netz 1 kg = 1.20 Normalpreis 3.49 AKTION 2.99
        Rispentomaten Italien, Kl. I kg-Preis Normalpreis 2.79 AKTION 1.99
        Wassermelone, kernarm Spanien, Kl. I Stück Normalpreis 4.99 AKTION 3.99
        Bio-Zitronen Spanien, Kl. II 500-g-Netz 1 kg = 1.98 Normalpreis 1.29 AKTION 0.99
        ---
        Super Sparer!
        Deutsche Markenbutter Mildgesäuert oder Süßrahmbutter 250-g-Packung 100 g = 0.52 Normalpreis 1.89 AKTION 1.29
        Mortadella Classica Italienische Mortadella, in Scheiben 150-g-Packung 100 g = 1.33 Normalpreis 2.49 AKTION 1.99
        Salami Sticks Classic oder Pikant je 100-g-Packung Normalpreis 1.79 AKTION 1.49
        Frische Vollmilch länger haltbar, 3,5 % Fett 1-L-Packung Normalpreis 1.15 AKTION 0.95 (2 Stück für 1.80)
        Speisequark Magerstufe 500-g-Becher 1 kg = 1.76 Normalpreis 0.99 AKTION 0.88
        Bio Eier 10 Stück Packung Normalpreis 3.29 AKTION 2.99 (Gültig bis Sa 1.6.)
        Coca-Cola Classic 1,25-L-Flasche zzgl. Pfand 0.25 1 L = 0.79 Normalpreis 1.29 AKTION 0.99
        Red Bull Energy Drink 250-ml-Dose zzgl. Pfand 0.25 100 ml = 0.38 Normalpreis 1.19 AKTION 0.95
        """
        
        # Grocery list is not used by the new prompt but the function signature still requires it.
        test_grocery_list_dummy = "Not used in this test."
        
        print("\n--- Calling get_ai_analysis ---")
        analysis_result = get_ai_analysis(test_api_key, test_grocery_list_dummy, sample_brochure_text)
        
        print("\n--- Test Result ---")
        print(f"Status: {analysis_result.get('status')}")
        
        if analysis_result.get("status") == "success":
            print("AI Response (should be JSON string):")
            # Try to pretty-print if it's valid JSON
            try:
                parsed_json = json.loads(analysis_result["ai_response"])
                print(json.dumps(parsed_json, indent=2, ensure_ascii=False))
            except json.JSONDecodeError:
                print("Response was not valid JSON, printing raw:")
                print(analysis_result["ai_response"])
        elif analysis_result.get("status") == "error":
            print(f"Error Message: {analysis_result.get('message')}")
            if "ai_raw_response" in analysis_result:
                print(f"AI Raw Response (on error): {analysis_result['ai_raw_response']}")
            if "details" in analysis_result:
                print(f"Details: {analysis_result['details']}")
        
        print("\n--- End of Test ---")
        print("Note: The grocery_list argument is currently ignored by the prompt in get_ai_analysis.")
        print("The focus is on extracting all deals from the brochure content into a structured JSON format.")
```
