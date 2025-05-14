from flask import Flask, jsonify, request
import requests
from requests.exceptions import Timeout, ConnectionError

app = Flask(__name__)

# Use a dictionary as a cache
products = {}

def analyze_ingredients(ingredients_text):
    """
    Analyzes a text string of ingredients and categorizes them as "good" or "bad".
    """
    good_ingredients = []
    bad_ingredients = []
    if ingredients_text:
        ingredients = [ing.strip() for ing in ingredients_text.split(',')]
        for ingredient in ingredients:
            if any(bad_word in ingredient.lower() for bad_word in
                   ["artificial", "high fructose", "hydrogenated", "msg", "sodium benzoate", "yellow",
                    "added sugar", "artificial color", "artificial flavor"]):
                bad_ingredients.append(ingredient)
            elif any(good_word in ingredient.lower() for good_word in
                     ["whole", "vitamin", "mineral", "fiber", "organic", "natural"]):
                good_ingredients.append(ingredient)
            else:
                pass
    return good_ingredients, bad_ingredients

@app.route('/product/<string:barcode>', methods=['GET'])
def get_product_info(barcode):
    """
    Retrieves product information based on the barcode, prioritizing the Open Food Facts API.
    """
    if barcode in products:
        return jsonify(products[barcode])  # Return cached data if available

    try:
        # Fetch product data from Open Food Facts with a timeout
        response = requests.get(f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json", timeout=10)  # 10-second timeout
        response.raise_for_status()
        data = response.json()

        if data["status"] == 1:
            product_name = data["product"].get("product_name", "Product Name Not Found")
            ingredients_text = data["product"].get("ingredients_text", "")
            (good_ingredients, bad_ingredients) = analyze_ingredients(ingredients_text)
            image_url = data["product"].get("image_url", None)  # Get the image URL

            product_data = {
                "name": product_name,
                "ingredients": ingredients_text,
                "good_ingredients": good_ingredients,
                "bad_ingredients": bad_ingredients,
                "image_url": image_url,  # Include the image URL in the response
            }
            products[barcode] = product_data
            return jsonify(product_data)
        else:
            return jsonify({"message": "Product not found in Open Food Facts"}), 404

    except (Timeout, ConnectionError) as e:
        return jsonify({"message": f"Error connecting to Open Food Facts: {e}"}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({"message": f"Error fetching data: {e}"}), 500
    except KeyError as e:
        return jsonify({"message": f"Error processing data from Open Food Facts: {e}.  Check the data structure."}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0') # Listen on all interfaces