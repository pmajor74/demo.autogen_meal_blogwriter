from autogen_agentchat.agents import AssistantAgent

def create_meal_nutrition_agent(recipes_to_generate, model_client):
    
    meal_nutrition_agent_prompt = f"""
    You are a Meal and Nutrition Agent. Your role is to fetch meal recipes and nutritional information for ingredients, and compile the data as instructed.

    TASK REQUIREMENTS:
    - You MUST fetch EXACTLY {recipes_to_generate} recipes - no more, no less
    - Each recipe MUST include the original ingredients with their measurements
    - You MUST fetch nutritional information for each ingredient
    - You MUST structure the data correctly for the software engineer to use

    TOOL DESCRIPTIONS:
    - get_random_recipe: Returns random meal recipes. Use get_random_recipe({recipes_to_generate}) to fetch EXACTLY {recipes_to_generate} recipes.
    - get_nutrition_info: Returns nutritional information for ingredients.
    """

    meal_nutrition_agent_prompt += """
    EXACT DATA STRUCTURE REQUIRED:
    {
        "Recipe Name 1": {
            "source": "URL",
            "thumb": "image URL",
            "instructions": "full instructions",
            "ingredients": [
                "1 cup flour",
                "2 eggs",
                "etc."
            ],
            "nutrition_data": {
                "flour": {nutrition details},
                "eggs": {nutrition details}
            },
            "total_nutrition": {calculated totals}
        },
        "Recipe Name 2": { ... },
        "Recipe Name 3": { ... }
    }
    """

    meal_nutrition_agent_prompt += f"""

    Step-by-step process:
    1. Call get_random_recipe({recipes_to_generate}) to get EXACTLY {recipes_to_generate} recipes
    2. For each recipe, extract the list of ingredients with their measurements
    3. For each ingredient, call get_nutrition_info to get nutritional data
    4. Calculate total nutrition values for each recipe
    5. Structure ALL data according to the format above
    6. Verify you have EXACTLY {recipes_to_generate} complete recipes before responding
    7. Return the COMPLETE structured data for all {recipes_to_generate} recipes in a single message

    CRITICAL: ALWAYS return EXACTLY {recipes_to_generate} recipes with COMPLETE data.
    """
        
    meal_nutrition_agent = AssistantAgent(
        name="meal_nutrition_agent",
        description="Responsible for fetching meal recipes and nutrition information.",        
        system_message=meal_nutrition_agent_prompt,
        model_client=model_client,
        tools=[get_nutrition_info, get_random_recipe],
    )
    
    return meal_nutrition_agent


# --------------------------------------------------------------------------------------------------------------------------------
# Agent Tools
# --------------------------------------------------------------------------------------------------------------------------------

def get_random_recipe(count: int) -> dict:
    """
    Get a specified number of random meal recipes from the MealDB API, where each recipe has non-empty strSource and strMealThumb fields. The recipes are returned in a simplified format.

    Args:
        count (int): The number of random recipes to retrieve.

    Returns:
        dict: A dictionary with a "meals" key containing a list of simplified recipe dictionaries. Each simplified recipe includes:
            - idMeal: The ID of the meal.
            - strMeal: The name of the meal.
            - strInstructions: The complete cooking instructions.
            - thumb: The URL of the meal thumbnail.
            - strYoutube: The YouTube link for the recipe.
            - ingredients: A list of strings, each representing an ingredient with its measure.
    """
    import requests

    api_url = 'https://www.themealdb.com/api/json/v1/1/random.php'
    simplified_meals = []

    while len(simplified_meals) < count:
        response = requests.get(api_url)
        if response.status_code == requests.codes.ok:
            data = response.json()
            if "meals" in data and data["meals"]:
                meal = data["meals"][0]
                if isinstance(meal, dict):
                    # Check strSource and strMealThumb
                    source:str = meal.get("strSource", "") or ""
                    thumb:str = meal.get("strMealThumb", "") or ""
                    if source is not None and thumb is not None:
                        # Transform the meal into simplified format
                        simplified_meal = {
                            "idMeal": meal.get("idMeal", ""),
                            "strMeal": meal.get("strMeal", ""),
                            "strInstructions": meal.get("strInstructions", "").replace("\r\n", "<br>"),
                            "thumb": thumb,
                            "strYoutube": meal.get("strYoutube", ""),
                            "source": source,
                            "ingredients": []
                        }
                        # Combine ingredients and measures
                        for i in range(1, 21):
                            ingredient = meal.get(f"strIngredient{i}", "")
                            measure = meal.get(f"strMeasure{i}", "")
                            if ingredient:
                                simplified_meal["ingredients"].append(f"{measure} {ingredient}")
                            else:
                                break
                        simplified_meals.append(simplified_meal)
        else:
            print("Error:", response.status_code, response.text)

    return {"meals": simplified_meals}


def get_nutrition_info(query: str) -> dict:
    """
    Retrieves nutrition information for a given food query from the USDA FoodData Central API.
    
    Args:
        query (str): The food query (e.g., "75g Butter", "1kg Leek", "1 Egg").
    
    Returns:
        dict: A dictionary containing simplified nutrition data on success, e.g.:
        {
            "calories": 537.75,
            "carbohydrates": 0.05,
            "protein": 0.64,
            "total_fat": 60.75
        }
        or, for non-critical errors (e.g., no food found, no nutrient data):
        {
            "calories": 0.0,
            "carbohydrates": 0.0,
            "protein": 0.0,
            "total_fat": 0.0
        }
        or, for critical errors (e.g., API key missing, network issues):
        {
            "error": "Detailed error message describing the issue"
        }
    """
    
    import requests
    import os
    import re
    import json
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv('../.env')
    API_KEY = os.environ.get("USDA_FOOD_API_KEY")

    # Default zeroed-out response for non-critical errors with fixed order
    ZERO_NUTRITION = {
        "calories": 0.0,
        "carbohydrates": 0.0,
        "protein": 0.0,
        "total_fat": 0.0
    }

    # Input validation
    if not query or not isinstance(query, str) or not query.strip():
        return ZERO_NUTRITION

    if not API_KEY:
        return {"error": "USDA_FOOD_API_KEY not found in environment variables"}

    # Nutrient IDs from USDA documentation
    NUTRIENT_MAP = {
        "calories": 1008,  # Energy in kcal
        "total_fat": 1004,  # Total lipid (fat)
        "protein": 1003,    # Protein
        "carbohydrates": 1005,  # Carbohydrate, by difference
    }

    # Helper function to parse the input query
    def parse_input(query: str):
        """Parse query into quantity, unit, and food name."""
        pattern = r"(\d+/\d+|\d*\.?\d+)\s*(\w+)?\s*(.*)"
        match = re.match(pattern, query)
        if match:
            quantity_str, unit, food_name = match.groups()
            try:
                quantity = eval(quantity_str) if '/' in quantity_str else float(quantity_str)
                if quantity <= 0:
                    return None, None, None, "Quantity must be positive"
            except Exception as e:
                return None, None, None, f"Failed to parse quantity '{quantity_str}': {str(e)}"
            unit = unit.lower() if unit else "g"
            food_name = food_name
            if not food_name:
                return None, None, None, "No food name provided"
        else:
            quantity = 1.0
            unit = "g"
            food_name = query
            if not food_name:
                return None, None, None, "No valid food name extracted"
        return quantity, unit, food_name, None

    # Helper function to convert quantity to grams
    def convert_to_grams(quantity, unit):
        """Convert quantity and unit to grams."""
        quantity = float(quantity)
        unit = unit.lower() if unit else "g"
        conversions = {
            "g": 1,
            "kg": 1000,
            "mg": 0.001,
            "ml": 1,  # Approximation: 1ml ≈ 1g (adjust for density if needed)
            "l": 1000,
            "oz": 28.3495,
            "lb": 453.592,
            "tsp": 5,
            "tbsp": 15,
            "cup": 240
        }
        return quantity * conversions.get(unit, 1)  # Default to 1 if unit unrecognized

    # Helper function to extract simple nutrition data with fixed order
    def get_simple_nutrition(nutrition_list):
        """Extract specified nutrients and scale them, returning in fixed order."""
        # Temporary storage for nutrient values
        temp_nutrition = {}
        for nutrient in nutrition_list:
            if 'nutrient' in nutrient:
                nutrient_id = nutrient['nutrient']['id']
                amount = float(nutrient.get('amount', 0))
                for name, id in NUTRIENT_MAP.items():
                    if nutrient_id == id:
                        temp_nutrition[name] = amount

        # Construct result with fixed order
        simple_nutrition = {
            "calories": temp_nutrition.get("calories", 0.0),
            "carbohydrates": temp_nutrition.get("carbohydrates", 0.0),
            "protein": temp_nutrition.get("protein", 0.0),
            "total_fat": temp_nutrition.get("total_fat", 0.0)
        }
        return simple_nutrition

    # Main logic with error handling
    try:
        # Parse input
        input_quantity, input_unit, food_name, parse_error = parse_input(query)
        if parse_error:
            return ZERO_NUTRITION  # Return zeros instead of error for non-critical issues

        # Search for food
        try:
            response = requests.get(
                f'https://api.nal.usda.gov/fdc/v1/foods/search?api_key={API_KEY}&pageSize=1&pageNumber=1&query={food_name}',
                timeout=10
            )
            response.raise_for_status()
            search_results = response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"API search request failed for '{food_name}': {str(e)}"}
        except json.JSONDecodeError as e:
            return {"error": f"Failed to decode search JSON for '{food_name}': {str(e)}"}

        if not search_results.get('foods'):
            return ZERO_NUTRITION  # Return zeros if no food is found

        food_id = search_results['foods'][0]['fdcId']

        # Get food details
        try:
            response = requests.get(
                f'https://api.nal.usda.gov/fdc/v1/food/{food_id}?api_key={API_KEY}',
                timeout=10
            )
            response.raise_for_status()
            food_details = response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"API details request failed for food ID {food_id}: {str(e)}"}
        except json.JSONDecodeError as e:
            return {"error": f"Failed to decode details JSON for food ID {food_id}: {str(e)}"}

        # Convert quantity to grams
        total_grams = convert_to_grams(input_quantity, input_unit)
        if total_grams <= 0:
            return ZERO_NUTRITION  # Return zeros for invalid grams

        # Scale nutrition to total_grams (USDA data is per 100g)
        nutrition_per_100g = food_details.get('foodNutrients', [])
        if not nutrition_per_100g:
            return ZERO_NUTRITION  # Return zeros if no nutrient data

        scale_factor = total_grams / 100
        for nutrient in nutrition_per_100g:
            if 'amount' in nutrient:
                nutrient['amount'] = float(nutrient['amount']) * scale_factor

        # Extract simple nutrition data with fixed order
        simple_nutrition = get_simple_nutrition(nutrition_per_100g)
        return simple_nutrition

    except Exception as e:
        return {"error": f"Unexpected error in get_nutrition_info for '{query}': {str(e)}"}
