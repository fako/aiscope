import requests
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from extract_ingredients.parser import IngredientParser
from extract_ingredients.data import INGREDIENTS_HTML_SNIPPET, RECIPE_URL, HEAD_HTML


def main(input_data):
    response = requests.get(input_data["url"])
    if response.status_code != 200:
        return []
    html_data = str(response.content)

    # Create an instance of the parser and feed HTML data
    parser = IngredientParser()
    parser.feed(html_data)

    # Retrieve and print the list of ingredients
    ingredients = parser.get_ingredients()
    print(ingredients)
    print(parser.title)
    print(parser.description)

    # Fetch the amount of servings
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    response = requests.post(
        "https://api.foodinfluencersunited.nl/api/public/r2b/recipe/get",
        json={"url": input_data["url"], "url_type": "canonical"},
        headers=headers
    )
    data = response.json()
    number_of_servings = data["data"]["numberOfServings"]
    print(number_of_servings)


if __name__ == "__main__":
    main({"url": RECIPE_URL})
