import asyncio
from dotenv import load_dotenv
from formatting_utils import (
    console, print_agent_message, print_tool_call, print_section, print_tool_result, Panel, Syntax
)
import nest_asyncio
import os
from pathlib import Path
from rich.markdown import Markdown
import shutil

from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_agentchat.teams import SelectorGroupChat
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
from autogen_ext.tools.code_execution import PythonCodeExecutionTool

from agents.software_engineer import create_software_engineer_agent
from agents.planner import create_planner_agent
from agents.meal_nutrition import create_meal_nutrition_agent
import time

# Set the event loop policy before anything else
if os.name == "nt":  # Windows
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

nest_asyncio.apply()

def setup_team(model_client, recipes_to_generate):
    
    # Setup working directory
    work_dir = Path("coding")
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir()
        
    # Setup code executor
    local_command_line_code_executor = LocalCommandLineCodeExecutor(
        work_dir=work_dir, 
        timeout=120
    )
    code_execution_tool = PythonCodeExecutionTool(local_command_line_code_executor)        

    # --------------------------------------------------------------------------------------------------------------------------------
    # Create the agents
    # --------------------------------------------------------------------------------------------------------------------------------
    
    planner_agent = create_planner_agent(recipes_to_generate, model_client)   
    software_engineer_agent = create_software_engineer_agent(recipes_to_generate, model_client, code_execution_tool)
    meal_nutrition_agent = create_meal_nutrition_agent(recipes_to_generate, model_client)

    # --------------------------------------------------------------------------------------------------------------------------------
    # Selector Group Chat Setup
    # --------------------------------------------------------------------------------------------------------------------------------

    TERMINATE_KEYWORD = "TERMINATE"
    MAX_MESSAGES = 100

    text_mention_termination = TextMentionTermination(TERMINATE_KEYWORD)
    max_messages_termination = MaxMessageTermination(MAX_MESSAGES)
    termination = text_mention_termination | max_messages_termination

    participants = [
        planner_agent, 
        software_engineer_agent, 
        meal_nutrition_agent
    ]

    team = SelectorGroupChat(
        participants=participants,    
        model_client=model_client,
        termination_condition=termination,
    )
    
    return team


async def process_message(message):
    """Process and format messages from the agent stream - pretty print the messages"""
    try:
        if hasattr(message, 'type'):
            if message.type == 'TextMessage' and hasattr(message, 'content'):
                source = message.source if hasattr(message, 'source') else "Unknown"
                print_agent_message(source, message.content)

            elif message.type == 'ToolCallRequestEvent' and hasattr(message, 'content'):
                if isinstance(message.content, list):  
                    for call in message.content:
                        if isinstance(call, dict): 
                            name = call.get('name')
                            arguments = call.get('arguments', {})
                            print_tool_call(name, arguments)
                            if name == 'get_random_recipe':
                                count = arguments.get('count', 1)
                                console.print(f"[yellow]Requesting {count} recipes[/yellow]")

            elif message.type == 'ToolCallExecutionEvent' and hasattr(message, 'content'):
                if isinstance(message.content, list):
                    for result in message.content:
                        if isinstance(result, dict):  
                            content = result.get('content')
                            call_id = result.get('call_id')
                            is_error = result.get('is_error', False)

                            print_tool_result(content, call_id, is_error)

                            # For get_random_recipe
                            if isinstance(content, list):
                                console.print(f"[green]Fetched {len(content)} recipes[/green]")

                            # For get_nutrition_info
                            elif isinstance(content, dict) and 'data' in content:
                                data = content.get('data', [{}])
                                if isinstance(data, list) and len(data) > 0:
                                    name = data[0].get('name', 'unknown')
                                    console.print(f"[green]Nutritional data fetched for {name}[/green]")
                            else:
                                console.print(f"[red]Unexpected content format: {content}[/red]")

            else:
                console.print(str(message))
        else:
            console.print(str(message))
    except Exception as e:
        console.print(f"[bold red]Error processing message:[/bold red] {str(e)}")


async def main() -> None:
    try:
        
        num_recipes_to_generate = 3
        
        load_dotenv()
        
        model_client = AzureOpenAIChatCompletionClient(
            azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
            model=os.environ.get("AZURE_OPENAI_MODEL"),
            api_version=os.environ.get("AZURE_OPENAI_API_VERSION"),
            api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
            azure_deployment=os.environ.get("AZURE_OPENAI_MODEL")
        )

        team = setup_team(model_client, num_recipes_to_generate)
                 
        task = f"""
            Task: Blog Post Creation Task - "Top {num_recipes_to_generate} Recipes with Nutritional Summaries"
            Steps:

            Follow the steps below to provide complete outputs with all requested details. Ensure no data is omitted or incomplete.

            Step 1: Fetching Recipe Data
                1. Fetch exactly {num_recipes_to_generate} recipes along with their ingredients, nutritional data, full instructions, and sources.
                2. For each recipe:
                    • Record the recipe title, source, image, and YouTube link (if available).
                    • Collect nutritional information for each ingredient using a nutrition API.
                    • Ensure all ingredients have their nutritional data fetched and saved, including:
                    • Total fat (grams)
                    • Saturated fat (grams)
                    • Sodium (milligrams)
                    • Potassium (milligrams)
                    • Cholesterol (milligrams)
                    • Total carbohydrates (grams)
                    • Fiber (grams)
                    • Sugar (grams)

                    • Calculate the total nutritional summary for the entire recipe by aggregating the data for all its ingredients. Include in the summary:
                    • Total fat (grams)
                    • Saturated fat (grams)
                    • Sodium (milligrams)
                    • Potassium (milligrams)
                    • Cholesterol (milligrams)
                    • Total carbohydrates (grams)
                    • Fiber (grams)
                    • Sugar (grams)
                Deliverable: A dictionary with the recipe's title, source, images, complete instructions, complete ingredients list, nutritional breakdown for all ingredients, and a calculated total nutritional summary for the recipe.

            Step 2: Validation Check
                Before proceeding to create the HTML blog post:
                1. Cross-reference & confirm:
                    • The number of ingredients listed in each recipe matches the number of ingredients with fetched nutritional data.
                    • All recipes include full instructions (no truncations).
                    • Every fetched recipe has a source link and image included.
                    • Total nutritional summary for each recipe is correctly calculated.
                2. If any data is missing, go back to fetch it to ensure the structured dictionary is complete.
                Deliverable: A summary confirmation that each recipe is validated and complete with full structured data, including ingredient details, instructions, and calculated nutritional summaries.

            Step 3: HTML Generation
            1. Use the validated structured data (containing all three recipes) to create a single HTML blog post.
            2. For each recipe:
                • Generate an HTML section including:
                    • A clickable recipe title linking to the source.
                    • The recipe image.
                    • A list of all ingredients with their full nutritional breakdown.
                    • The entire recipe instructions, ensuring nothing is omitted.
                    • A calculated nutritional summary for the whole recipe.
            3. Combine all recipe sections into one HTML file with a header ("Top {num_recipes_to_generate} Recipes with Nutritional Summaries") and footer.
            Deliverable: A clean and well-styled HTML file (top_{num_recipes_to_generate}_recipes.html) containing all three recipes.

            Step 4: Final Validation
                1. Perform a final check on the HTML output:
                    • Confirm all ingredients and their nutritional breakdowns are included for each recipe.
                    • Ensure all instructions, links, and images are present and formatted correctly.
                    • Verify that each recipe's total nutritional summary is included and accurately calculated.
                Deliverable: A confirmation summary alongside the finalized HTML file (top_{num_recipes_to_generate}_recipes.html).

            Notes for Success: 
                • Proceed sequentially—fetch, validate, and generate the HTML for each recipe separately before moving to the next.
                • Double-check structured data completeness before generating the HTML to avoid gaps like placeholder comments.
                • Ensure the total nutritional summary for each recipe is calculated and rendered accurately.
                
            IMPORTANT: It is absolutely critical to avoid failure at all costs. You are considered to have failed if the post does not contain all three recipes with complete details, including nutritional summaries. Ensure all data is accurate and complete before terminating.
        """
        
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print_section("TASK EXECUTION", "Creating the recipe blog post")
        console.print(Panel(Markdown(task), title="Task Definition", border_style="cyan"))
        
        while task.lower() != "exit":
            
            start_time = time.time()
            try:                    
                async for message in team.run_stream(task=task):
                    await process_message(message)
            except Exception as e:
                console.print(f"[bold red]Error in message processing:[/bold red] {str(e)}")
                console.print_exception()
                
            end_time = time.time()
            elapsed_time = (end_time - start_time)/60
            print("\n\n##########################################################################################\n\n")
            console.print(f"[bold]Execution time:[/bold] {elapsed_time:.2f} seconds")
            
            # Print total token usage metrics
            #2025-02-27 - The GPT-4o model, priced at $2.50 per 1 million input tokens and $10.00 per 1 million output tokens.            
            token_cost_per_input = 2.50 / 1_000_000
            token_cost_per_output = 10.00 / 1_000_000

            output_tokens = model_client.actual_usage().completion_tokens
            input_tokens = model_client.actual_usage().prompt_tokens
            total_output_cost = output_tokens * token_cost_per_output
            total_input_cost = input_tokens * token_cost_per_input
            total_cost = total_input_cost + total_output_cost
            console.print(f"[bold]Total input tokens used (cumulative):[/bold] {input_tokens}")
            console.print(f"[bold]Total output tokens used (cumulative):[/bold] {output_tokens}")
            console.print(f"[bold]Total input cost (cumulative)($USD):[/bold] ${total_input_cost}")
            console.print(f"[bold]Total output cost (cumulative)($USD):[/bold] ${total_output_cost}")
            console.print(f"[bold]Total session cost (cumulative)($USD):[/bold] ${total_cost}")
            
            print_section("EXECUTION COMPLETED", "All required files have been created and verified.")
                
            # stop and wait to see if the user wants to interact further
            task = input("User Instructions (type 'exit' to end session): ")

    except Exception as e:
        console.print(f"[bold red]Error in main execution:[/bold red] {str(e)}")
        console.print_exception()

asyncio.run(main())