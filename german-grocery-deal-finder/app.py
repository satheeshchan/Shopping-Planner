from flask import Flask, request, jsonify, render_template
import os
import json # For parsing AI response
import re # For regex operations in unit standardization
from ai_client import get_ai_analysis, match_item_to_brochure_offers # Import AI client functions
from pdf_processor import extract_text_from_pdf # Import PDF processing function

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Helper Functions for Unit Standardization ---

def parse_price(price_str: str) -> float | None:
    if not price_str or not isinstance(price_str, str):
        return None
    try:
        # Replace comma with dot for European formats, remove other non-numeric (except dot)
        cleaned_price = price_str.replace('.', '').replace(',', '.') 
        # Remove currency symbols or other text if any left (e.g. "€ 2.99", "ca. 1.99")
        cleaned_price = re.sub(r"[^0-9\.]", "", cleaned_price)
        if not cleaned_price: return None
        return float(cleaned_price)
    except ValueError:
        return None

def extract_quantity_and_unit_from_string(text: str) -> tuple[float | None, str | None, int | None]:
    """
    Extracts quantity, unit, and item count from a string.
    Returns: (quantity, unit, item_count_for_multipack)
    Example: "500g" -> (500, "g", 1)
             "2 x 1.5L" -> (1.5, "L", 2)
             "6er Pack" -> (1, "Stück", 6)
             "1 Stk" -> (1, "Stück", 1)
    """
    if not text: text = ""
    text = text.lower()

    # For "2 x 1.5L" type formats or "3x70g"
    multipack_match = re.search(r"(\d+)\s*x\s*(\d+(?:[,\.]\d+)?)\s*(kg|g|l|liter|ml|stk|stück|st)", text)
    if multipack_match:
        item_count = int(multipack_match.group(1))
        quantity = parse_price(multipack_match.group(2)) # Use parse_price for "1,5" etc.
        unit = multipack_match.group(3)
        if unit == "liter": unit = "l"
        if unit == "stück" or unit == "stk": unit = "Stück"
        return quantity, unit, item_count

    # For "500g", "1.5L", "1kg"
    quantity_match = re.search(r"(\d+(?:[,\.]\d+)?)\s*(kg|g|l|liter|ml|stk|stück|st)", text)
    if quantity_match:
        quantity = parse_price(quantity_match.group(1))
        unit = quantity_match.group(2)
        if unit == "liter": unit = "l"
        if unit == "stück" or unit == "stk": unit = "Stück"
        return quantity, unit, 1 # Default item count is 1

    # For "6er Pack", "10er Tray" (number of items in a pack)
    item_count_match = re.search(r"(\d+)\s*(er)\s*(pack|pkg|tray|kiste|beutel|netz|schale)", text)
    if item_count_match:
        return 1, "Stück", int(item_count_match.group(1)) # Quantity 1 of "Stück", but item_count is N

    # For "Stück", "Packung" without explicit numbers (assume 1)
    if "stück" in text or "stk" in text or "st" in text: return 1, "Stück", 1
    if "packung" in text or "pkg" in text: return 1, "Packung", 1
    if "flasche" in text: return 1, "Flasche", 1
    if "bund" in text : return 1, "Bund", 1
    
    return None, None, 1 # Default item count is 1 if not a multipack

def standardize_offer_price(offer: dict) -> dict:
    """
    Calculates standardized unit price for an offer.
    Adds: 'calculated_price_float', 'comparable_unit', 'standardized_unit_price', 'standardization_notes'
    """
    product_name = offer.get("product_name", "")
    price_str = offer.get("price", "")
    unit_str = offer.get("unit", "") # e.g. "kg", "500g Packung", "Liter"
    condition_str = offer.get("offer_condition", "")  # e.g. "2 für 1.80€", "pro 100g"

    calculated_price = parse_price(price_str)
    offer['calculated_price_float'] = calculated_price
    offer['comparable_unit'] = unit_str # Default
    offer['standardized_unit_price'] = calculated_price # Default
    offer['standardization_notes'] = "Original price used."

    if calculated_price is None:
        offer['standardization_notes'] = "Could not parse price."
        return offer

    # Combine all text sources for quantity extraction
    search_text_for_quantity = f"{product_name} {unit_str} {condition_str}".lower()
    
    # 1. Check for "X für Y€" in conditions first
    condition_price_match = re.search(r"(\d+)\s*(?:stück|stk|packungen|pkg)?\s*(?:für|zum preis von|nur)\s*(\d+([,\.]\d+)?)", condition_str.lower())
    if condition_price_match:
        num_items_in_condition = int(condition_price_match.group(1))
        total_price_in_condition = parse_price(condition_price_match.group(2))
        if num_items_in_condition > 0 and total_price_in_condition is not None:
            calculated_price = total_price_in_condition / num_items_in_condition
            offer['calculated_price_float'] = calculated_price # This is now price per item in the deal
            offer['standardization_notes'] = f"Original: {num_items_in_condition} for {total_price_in_condition}€. Effective price per item: {calculated_price:.2f}€."
            # Now, try to standardize this new item price further if its unit is known (e.g. each item is 500g)
            # Fallthrough to next logic with the new calculated_price for one item.
            # The unit_str still describes one item.

    # 2. Extract quantity and unit from combined text
    # The `unit_str` from AI might be "kg", "Liter", but also "500g Packung", "1.5L Flasche"
    # The `product_name` might also contain "6er Pack" etc.
    
    quantity, parsed_unit, items_in_pack = extract_quantity_and_unit_from_string(search_text_for_quantity)
    
    original_unit_info = f"Unit: '{unit_str}', Product: '{product_name}', Cond: '{condition_str}'"
    notes_suffix = ""

    if parsed_unit and quantity is not None:
        current_price_for_quantity = calculated_price # This is price for 'quantity' of 'parsed_unit' * 'items_in_pack'
        
        if items_in_pack > 1 and parsed_unit == "Stück": # e.g. 6er pack, price is for 6 items
            current_price_for_quantity = current_price_for_quantity / items_in_pack
            notes_suffix += f" Priced per item from {items_in_pack}-pack."
            # quantity is already 1 for "Stück", so this is price per single piece.
        
        if parsed_unit == "g" or parsed_unit == "gramm":
            if quantity > 0:
                offer['standardized_unit_price'] = (current_price_for_quantity / quantity) * 1000
                offer['comparable_unit'] = "kg"
                offer['standardization_notes'] = f"Converted to price per kg from {quantity}g.{notes_suffix} {original_unit_info}"
        elif parsed_unit == "ml":
            if quantity > 0:
                offer['standardized_unit_price'] = (current_price_for_quantity / quantity) * 1000
                offer['comparable_unit'] = "L"
                offer['standardization_notes'] = f"Converted to price per L from {quantity}ml.{notes_suffix} {original_unit_info}"
        elif parsed_unit == "kg":
            if quantity > 0: # e.g. "0.5 kg"
                offer['standardized_unit_price'] = current_price_for_quantity / quantity
                offer['comparable_unit'] = "kg"
                offer['standardization_notes'] = f"Price per kg (original {quantity}kg).{notes_suffix} {original_unit_info}"
        elif parsed_unit == "l" or parsed_unit == "liter":
             if quantity > 0: # e.g. "0.75 L"
                offer['standardized_unit_price'] = current_price_for_quantity / quantity
                offer['comparable_unit'] = "L"
                offer['standardization_notes'] = f"Price per L (original {quantity}L).{notes_suffix} {original_unit_info}"
        elif parsed_unit == "Stück" or parsed_unit == "Packung" or parsed_unit == "Flasche" or parsed_unit == "Bund":
            if quantity > 0: # quantity is usually 1 here unless "2 Stück" was parsed
                offer['standardized_unit_price'] = current_price_for_quantity / quantity 
                offer['comparable_unit'] = parsed_unit # "Stück" or "Packung" etc.
                offer['standardization_notes'] = f"Price per {parsed_unit} (original {quantity} {parsed_unit}).{notes_suffix} {original_unit_info}"
        else: # Unknown parsed unit, or quantity was None
            if not offer['standardization_notes'] or offer['standardization_notes'] == "Original price used.":
                 offer['standardization_notes'] = f"Could not fully standardize. {original_unit_info}"

    elif "pro 100g" in condition_str.lower() or "je 100g" in condition_str.lower() or "100g =" in unit_str.lower():
        # Price is given per 100g
        offer['standardized_unit_price'] = calculated_price * 10 # Price per 1kg
        offer['comparable_unit'] = "kg"
        offer['standardization_notes'] = f"Converted to price per kg from 100g price. {original_unit_info}"
    elif "pro kg" in condition_str.lower() or "je kg" in condition_str.lower() or "/kg" in unit_str.lower():
        offer['standardized_unit_price'] = calculated_price
        offer['comparable_unit'] = "kg"
        offer['standardization_notes'] = f"Price is per kg. {original_unit_info}"
    # Add more rules as needed, e.g. for "pro Liter"

    # Ensure standardized price is rounded
    if offer.get('standardized_unit_price') is not None:
        try:
            offer['standardized_unit_price'] = round(float(offer['standardized_unit_price']), 2)
        except (ValueError, TypeError):
            # If it somehow became non-numeric, revert to calculated_price_float
            offer['standardized_unit_price'] = offer['calculated_price_float']


    return offer

# --- End of Helper Functions ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_brochure', methods=['POST'])
def process_brochure():
    brochure_file = request.files.get('brochure_pdf')
    grocery_list_str = request.form.get('grocery_list', '')
    api_key = request.form.get('api_key', '')

    if not api_key:
        return jsonify({"status": "error", "message": "API key is required"}), 400
    
    if not grocery_list_str: # User's grocery list
        return jsonify({"status": "error", "message": "Grocery list is required"}), 400

    brochure_content_for_ai = None
    pdf_filename_for_response = "N/A"

    if brochure_file and brochure_file.filename:
        filename = brochure_file.filename 
        pdf_filename_for_response = filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            brochure_file.save(file_path)
        except Exception as e:
            return jsonify({"status": "error", "message": f"Could not save PDF: {str(e)}"}), 500

        extracted_text = extract_text_from_pdf(file_path)
        if extracted_text is not None and extracted_text.strip():
            brochure_content_for_ai = extracted_text
        else:
            return jsonify({
                "status": "error", 
                "message": "Failed to extract substantial text from the uploaded PDF. It might be image-based, corrupted, or empty.",
                "pdf_filename": filename
            }), 400
    else:
        return jsonify({"status": "error", "message": "No PDF brochure file uploaded."}), 400

    if not brochure_content_for_ai: 
        return jsonify({"status": "error", "message": "Brochure content could not be determined for AI analysis."}), 500

    extraction_result = get_ai_analysis(api_key, grocery_list_str, brochure_content_for_ai) 

    if extraction_result.get("status") != "success":
        extraction_result['pdf_filename_processed'] = pdf_filename_for_response
        return jsonify(extraction_result), 500 

    all_brochure_offers_str = extraction_result.get("ai_response", "[]")
    all_brochure_offers = []
    try:
        all_brochure_offers = json.loads(all_brochure_offers_str)
        if not isinstance(all_brochure_offers, list):
            return jsonify({
                "status": "error", 
                "message": "AI successfully extracted brochure data, but it's not in the expected list format.",
                "ai_raw_response": all_brochure_offers_str, 
                "pdf_filename_processed": pdf_filename_for_response
            }), 500
    except json.JSONDecodeError:
        return jsonify({
            "status": "error", 
            "message": "Failed to parse the extracted brochure offers from AI (not valid JSON).",
            "ai_raw_response": all_brochure_offers_str, 
            "pdf_filename_processed": pdf_filename_for_response
        }), 500

    user_list_items = [item.strip() for item in grocery_list_str.splitlines() if item.strip()]
    
    matched_items_details = []
    unmatched_user_items = []
    
    if not all_brochure_offers:
        return jsonify({
            "status": "success_no_offers_found",
            "message": "No offers were extracted from the brochure. Cannot perform matching.",
            "all_brochure_offers": [], "user_shopping_list_matches": [], "unmatched_user_items": user_list_items,
            "pdf_filename_processed": pdf_filename_for_response
        })

    if not user_list_items: 
        # Standardize all extracted offers even if user list is empty, for display
        standardized_all_offers = [standardize_offer_price(offer.copy()) for offer in all_brochure_offers]
        return jsonify({
            "status": "success_no_user_items",
            "message": "User grocery list is empty. Extracted and standardized all offers from brochure.",
            "all_brochure_offers": standardized_all_offers,
            "user_shopping_list_matches": [], "unmatched_user_items": [],
            "pdf_filename_processed": pdf_filename_for_response
        })

    for user_item in user_list_items:
        if not user_item: 
            continue
        
        match_result_offer = match_item_to_brochure_offers(api_key, user_item, all_brochure_offers)
        
        if match_result_offer:
            if match_result_offer.get("status") == "error":
                unmatched_user_items.append({"user_item": user_item, "match_error": match_result_offer.get('message', 'Unknown matching error')})
            else:
                # Standardize the matched offer
                standardized_matched_offer = standardize_offer_price(match_result_offer.copy()) # Use .copy()
                matched_items_details.append({
                    "user_item": user_item,
                    "matched_offer": standardized_matched_offer 
                })
        else:
            unmatched_user_items.append({"user_item": user_item, "match_error": None})

    # Also standardize the full list of brochure offers for display
    standardized_all_brochure_offers = [standardize_offer_price(offer.copy()) for offer in all_brochure_offers]

    # --- Step 3: Calculate Total Cost and Prepare Summary ---
    total_cost_of_matched_items = 0.0
    for item_match in matched_items_details:
        offer = item_match.get("matched_offer", {})
        # Use standardized_unit_price if it's a per-item price, otherwise calculated_price_float.
        # This assumes quantity 1 for each user item.
        # A more sophisticated approach would involve user-defined quantities and better logic
        # to determine if standardized_unit_price is for a base unit (kg/L) or per piece.
        # For now, if comparable_unit is Stück, Packung, Flasche, Bund, assume it's price per item.
        # Otherwise, if it's kg/L, the 'standardized_unit_price' is per that base unit,
        # and we'd ideally need a typical quantity for the item (e.g. 1kg Tomaten, 0.5kg Hackfleisch).
        # As a simplification, we use 'calculated_price_float' which is the price for the pack/unit found.
        
        price_to_add = offer.get('calculated_price_float') # Default to the listed price for the item/pack
        
        # If the comparable unit is one of these, the standardized_unit_price is likely per single item
        # (especially if items_in_pack from extract_quantity_and_unit_from_string was > 1
        # or if condition_price_match resulted in price_per_item).
        # However, calculated_price_float has already been adjusted for "X für Y" deals to be per item.
        # So, calculated_price_float should generally be the price for the single unit/pack presented.
        
        if price_to_add is not None:
            total_cost_of_matched_items += price_to_add

    shopping_summary = {
        "total_cost_of_matched_items": f"{total_cost_of_matched_items:.2f}",
        "currency": "EUR", # Assuming EUR for German groceries
        "number_of_matched_items": len(matched_items_details),
        "number_of_unmatched_items": len(unmatched_user_items)
    }

    final_response_data = {
        "status": "success",
        "all_brochure_offers": standardized_all_brochure_offers,
        "user_shopping_list_matches": matched_items_details,
        "unmatched_user_items": unmatched_user_items,
        "shopping_summary": shopping_summary, # Added summary
        "pdf_filename_processed": pdf_filename_for_response
    }
    return jsonify(final_response_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
