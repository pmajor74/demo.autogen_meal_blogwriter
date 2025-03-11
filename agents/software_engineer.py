from autogen_agentchat.agents import AssistantAgent

# --------------------------------------------------------------------------------------------------------------------------------
# Agent
# --------------------------------------------------------------------------------------------------------------------------------

def create_software_engineer_agent(recipes_to_generate, model_client, code_execution_tool):
    software_engineer_prompt = f"""
    You are a Senior Software Engineer with deep understanding of Python. Your role is to write clean, functional Python code to solve the problems presented to you.
    If you write content to a file, make sure its utf-8.
    ** IMPORTANT ** - You will not repond to any tasks involving meals or nutrition data. You will only respond to tasks that require writing code.
    """

    software_engineer_agent = AssistantAgent(
        name="software_engineer_agent",
        description="""Responsible for writing and executing source code to solve problems. Can write code that saves and reads from files on the local file system.""",  
        system_message=software_engineer_prompt,
        model_client=model_client,
        tools=[code_execution_tool, read_file, write_file],
        reflect_on_tool_use=True
    )
        
    return software_engineer_agent


# --------------------------------------------------------------------------------------------------------------------------------
# Agent Tools
# --------------------------------------------------------------------------------------------------------------------------------

def read_file(filename: str) -> str:
    """
    Read the contents of file and return it as a string.
    
    Args:
        filename (str): Name of the file to read
    
    Returns:
        str: Contents of the file as a string
    
    Raises:
        FileNotFoundError: If the file doesn't exist
        IOError: If there's an error reading the file
    """
    import os
    
    try:        
        
        filepath = os.path.join("coding", filename)
        abs_filepath = os.path.abspath(filepath)
        print(f"##read_file: reading content from {abs_filepath}")
        # Check if file exists
        if not os.path.exists(abs_filepath):
            raise FileNotFoundError(f"File not found: {abs_filepath}")
        
        # Read and return the file contents
        with open(abs_filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        return content
        
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Error: {str(e)}")
    except Exception as e:
        raise IOError(f"Error reading file {filename}: {str(e)}")
    

def write_file(filename:str, content:str) -> dict:
    """
    Write content to a file in the working directory and verify it exists.
    
    Args:
        filename (str): Name of the file to create
        content (str): content to write to the file
    
    Returns:
        dict: Information about the operation including success status and file path
    """
    
    import os
    
    try:
        # Use the coding directory
        filepath = os.path.join("coding", filename)
        abs_filepath = os.path.abspath(filepath)
        
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(abs_filepath), exist_ok=True)
        
        print(f"##write_file: writing content to {abs_filepath}")
        
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
            "error": f"Error creating file {filename}: {str(e)} : Additional Info: {abs_filepath}\nError Details: {e}"
        }