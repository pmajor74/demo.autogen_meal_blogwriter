from autogen_agentchat.agents import AssistantAgent

# --------------------------------------------------------------------------------------------------------------------------------
# Agent
# --------------------------------------------------------------------------------------------------------------------------------

def create_software_engineer_agent(recipes_to_generate, model_client, code_execution_tool):
    software_engineer_prompt = f"""
    You are a Senior Software Engineer with deep understanding of Python. Your role is to write clean, functional Python code to solve the problems presented to you.

    CRITICAL HTML GENERATION REQUIREMENTS:
    1. You MUST create an HTML page displaying EXACTLY {recipes_to_generate} recipes
    2. For EACH recipe, you MUST include:
    - Recipe title with source link
    - Recipe image
    - List of ORIGINAL ingredients with measurements (not nutritional data)
    - Complete cooking instructions
    - Nutritional summary section (separate from ingredients)
    3. The HTML structure MUST clearly separate:
    - The ingredients list (showing measurements like "2 Eggs", "1 cup Flour")
    - The nutritional information (displayed in a separate section)

    COMMON ERRORS TO AVOID:
    - DO NOT display nutritional data in the ingredients list
    - DO NOT skip any recipes - ensure ALL {recipes_to_generate} recipes appear in the final HTML
    - DO NOT mix ingredient measurements with nutritional data

    PROPER HTML STRUCTURE EXAMPLE:
    ```html
    <div class="recipe">
    <h2><a href="source_url">Recipe Name</a></h2>
    <img src="image_url">
    
    <div class="ingredients">
        <h3>Ingredients:</h3>
        <ul>
        <li>2 Eggs</li>
        <li>1 tbsp Butter</li>
        </ul>
    </div>
    
    <div class="instructions">
        <h3>Instructions:</h3>
        <p>Full cooking instructions...</p>
    </div>
    
    <div class="nutrition-summary">
        <h3>Nutritional Summary:</h3>
        <p>Total Fat: 36.7g, etc...</p>
    </div>
    </div>

    VERIFICATION CHECKLIST:

    Does your HTML include ALL {recipes_to_generate} recipes?
    Does each recipe show ingredients WITH measurements?
    Does each recipe have its nutritional data in a SEPARATE section?
    Are all parts of each recipe (title, image, ingredients, instructions, nutrition) included?

    Only when you've verified these requirements should you write the HTML to a file.
    """

    software_engineer_agent = AssistantAgent(
        name="software_engineer_agent",
        description="Responsible for writing source code to solve problems, complete tasks and interact with APIs.",
        system_message=software_engineer_prompt,
        model_client=model_client,
        tools=[code_execution_tool, write_html_file],
        reflect_on_tool_use=True
    )
    
    return software_engineer_agent


# --------------------------------------------------------------------------------------------------------------------------------
# Agent Tools
# --------------------------------------------------------------------------------------------------------------------------------

def write_html_file(filename:str, content:str) -> dict:
    """
    Explicitly write HTML content to a file in the working directory and verify it exists.
    
    Args:
        filename (str): Name of the HTML file to create
        content (str): HTML content to write to the file
    
    Returns:
        dict: Information about the operation including success status and file path
    """
    
    import os
    
    try:
        # Ensure file has .html extension
        if not filename.endswith('.html'):
            filename = f"{filename}.html"
            
        # Use the coding directory
        filepath = os.path.join("coding", filename)
        abs_filepath = os.path.abspath(filepath)
        
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(abs_filepath), exist_ok=True)
        
        # Write the content to the file
        with open(abs_filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        # Verify the file exists
        file_exists = os.path.exists(abs_filepath)
        file_size = os.path.getsize(abs_filepath) if file_exists else 0
        
        return {
            "success": file_exists,
            "filepath": abs_filepath,
            "filesize": file_size,
            "message": f"File {'successfully written' if file_exists else 'failed to write'} to {abs_filepath}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error creating file {filename}: {str(e)}"
        }