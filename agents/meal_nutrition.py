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
                    if source is not None and source.strip() and thumb is not None and thumb.strip():
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
                            ingredient = meal.get(f"strIngredient{i}", "").strip()
                            measure = meal.get(f"strMeasure{i}", "").strip()
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
    Get nutrition information for the query specified.

    Args:
        query (str): This is the recipe item for which the nutrition information is needed. Example query: "1 cup brisket"
        
    Returns:
        dict: A dictionary containing either the nutritional data
    """
    import requests
    import json
    from dotenv import load_dotenv
    import os
    
    # Input validation
    if not query or not isinstance(query, str) or not query.strip():
        return {
            "success": False,
            "error": "Invalid query parameter",
            "data": [{
                "name": "unknown",
                "fat_total_g": 0,
                "fat_saturated_g": 0,
                "sodium_mg": 0,
                "potassium_mg": 0,
                "cholesterol_mg": 0,
                "carbohydrates_total_g": 0,
                "fiber_g": 0,
                "sugar_g": 0
            }]
        }
    
    try:
        load_dotenv('../.env')
        api_key = os.getenv('API_NINJAS_API_KEY')
        
        if not api_key:
            return {
                "success": False,
                "error": "API key not found",
                "data": [{
                    "name": query.split()[-1] if query.split() else "unknown",
                    "fat_total_g": 0,
                    "fat_saturated_g": 0,
                    "sodium_mg": 0,
                    "potassium_mg": 0,
                    "cholesterol_mg": 0,
                    "carbohydrates_total_g": 0,
                    "fiber_g": 0,
                    "sugar_g": 0
                }]
            }
        
        api_url = f'https://api.api-ninjas.com/v1/nutrition?query={query}'
        
        response = requests.get(
            api_url, 
            headers={'X-Api-Key': api_key}, 
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
        else:
            data = None
            
        return data
            
    except Exception:
        raise
