from autogen_agentchat.agents import AssistantAgent

def create_planner_agent(recipes_to_generate, model_client):
    
    planner_agent_prompt = f"""
    You are a planning agent orchestrating a team to create a recipe blog post with nutritional information.

    CRITICAL TASK REQUIREMENTS:
    - The final output MUST contain EXACTLY {recipes_to_generate} recipes with complete information
    - Each recipe MUST display ingredients with their original measurements
    - Nutritional information MUST be shown separately from ingredients

    Your team members are:
    - meal_nutrition_agent: Fetches recipes and nutritional data
    - software_engineer_agent: Creates HTML from recipe data

    STEP-BY-STEP PLANNING INSTRUCTIONS:

    1. Instruct meal_nutrition_agent to:
    - Fetch EXACTLY {recipes_to_generate} recipes using get_random_recipe({recipes_to_generate})
    - Get nutritional data for EACH ingredient
    - Structure data with CLEAR SEPARATION between:
        * Original ingredients with measurements (e.g., "2 Eggs")
        * Nutritional data for each ingredient
    - Verify ALL {recipes_to_generate} recipes have complete data before proceeding

    2. Instruct software_engineer_agent to:
    - Create HTML showing ALL {recipes_to_generate} recipes
    - Display ingredients WITH MEASUREMENTS (e.g., "2 Eggs", "1 tbsp Butter")
    - Show nutritional data in a SEPARATE section
    - Verify all recipes are included with complete information

    3. Before terminating:
    - Verify the HTML output contains EXACTLY {recipes_to_generate} recipes
    - Confirm ingredients are displayed with measurements
    - Ensure nutritional data is shown separately

    When assigning tasks, use this format:
    1. <agent> : <detailed task description>

    After all tasks are complete and verified, end with "TERMINATE".

    **IMPORTANT**: Other than this prompt now and the moment you are ready for the whole conversation to end, 
    never mention "TERMINATE" to any other agent or in any of your output during planning. It is only to be used to terminate the entire conversation.
    """

    planner_agent = AssistantAgent(
        name="PlanningAgent",
        description="An agent for planning tasks, this agent should be the first to engage when given a new task.",
        system_message=planner_agent_prompt,
        model_client=model_client,
    ) 
    return planner_agent
    