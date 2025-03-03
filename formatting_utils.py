import ast
import json
import re
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
import warnings

console = Console()

def format_function_arguments(arguments):
    """
    Formats function arguments dynamically for better readability.
    Supports dicts, lists, and single values.
    """
    args_obj = json.loads(arguments) 
    
    if isinstance(args_obj, dict):
        return ", ".join(f"{k}={repr(v)}" for k, v in args_obj.items())
    elif isinstance(args_obj, list):
        return ", ".join(map(repr, args_obj))
    else:
        return repr(args_obj)  # Handles single values like int, bool, str

async def process_message(message, source:str):
    """Process and format messages from the agent stream - pretty print the messages"""
    try:
        if type(message).__name__ == 'TextMessage' and hasattr(message, 'content'):
                source = message.source if hasattr(message, 'source') else "Unknown"
                print_agent_message(source, message.content)

        elif type(message).__name__ == 'MultiModalMessage' and hasattr(message, 'content'):
            print_agent_multimodal_message(source, message.content)
        elif type(message).__name__ == 'ToolCallRequestEvent' and hasattr(message, 'content'):
            if isinstance(message.content, list):  
                for call in message.content:
                    if type(call).__name__ == 'FunctionCall':
                        name = call.name                        

                        # Format arguments using the extracted function
                        args_str = format_function_arguments(call.arguments)

                        tool_use_message = f"[bold yellow]Function Call:[/bold yellow] {name}({args_str})"

                        console.print(Panel(
                            tool_use_message,
                            title=f"[bold yellow]Tool Use Function Call From agent:[/bold yellow][bold blue]{source}[/bold blue]",
                            border_style="blue"
                        ))
                            
        elif type(message).__name__ == 'ToolCallExecutionEvent' and hasattr(message, 'content'):
            # passing this for now, all the tool calls are printed in the ToolCallSummaryMessage
            # this event is useful to watch if you find function call summarization issues, but for the most part the summary message is the same as the tool call execution event
            pass            
            # if isinstance(message.content, list):
            #     for result in message.content:
            #         if type(result).__name__ == 'FunctionExecutionResult':
            #             print_tool_result(result.content, type(result).__name__, message.source, result.call_id, result.is_error)
            #         else:
            #             console.print(f"[red]Unexpected content format: {result.content}[/red]")
            # else:
            #     console.print(f"[red]Unexpected content format: type=={type(message.content).__name__} - content: {message.content}[/red]")
                
        elif type(message).__name__ == 'ToolCallSummaryMessage' and hasattr(message, 'content'):
            console.print(f"[bold yellow]############# Tool Use Function Call Summary From agent:[/bold yellow][bold blue]{source}[/bold blue]")            
            
            # preprocess the tool call summary data so that it can be printed in a more readable format
            lines = [line.strip() for line in message.content.splitlines() if line.strip()]
            literal = f"[{','.join(lines)}]"  # Wrap them in brackets and join with commas
            python_obj = ast.literal_eval(literal)  # Evaluate the string as a Python expression
            json_str = json.dumps(python_obj, indent=4)
            
            print_tool_result(json_str, type(message).__name__, message.source, "", is_error=False)            
        else:
            console.print(str(message))
    except Exception as e:
        console.print(f"[bold red]Error processing message:[/bold red] {str(e)}")

def format_json(data, title=None):
    """Pretty print JSON data with syntax highlighting"""
    try:
        
        python_obj = ast.literal_eval(data)
        json_str = json.dumps(python_obj, indent=4)

        # if there are any html <br> tags, replace with newlines for better formatting
        json_str = re.sub(r'(?i)<br\s*/?>', '\n', json_str)
        
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
        if title:
            return Panel(syntax, title=title, border_style="blue")
        return syntax
    
    except:
        # If it's not valid JSON, return as is
        return data

def print_section(title, subtitle=None):
    """Print a section header with optional subtitle"""
    console.print("\n")
    console.rule(f"[bold blue]{title}[/bold blue]", style="blue")
    
    if subtitle:
        console.print(f"[dim]{subtitle}[/dim]", justify="center")
    console.print("\n")

def print_tool_result(result, source:str, title: str,  call_id: str, is_error:bool=False):
    """Format tool results nicely"""
    style = "red" if is_error else "green"
    title = f"[bold {style}]source={source} - Function Result:[/bold {style}] {call_id[:10]}..."
    
    try:
        if isinstance(result, str):
            try:                
                content = format_json(result)

                console.print(Panel(
                    content,
                    title=title,
                    border_style=style
                ))
            except Exception as e:
                console.print(Panel(
                    result,
                    title=title,
                    border_style=style
                ))
        else:
            console.print(Panel(
                format_json(result),
                title=title,
                border_style=style
            ))
    except:
        console.print(Panel(
            str(result),
            title=title,
            border_style=style
        ))

def print_agent_message(name, content):
    """Format agent messages nicely"""
    formatted_content = content.replace("\\n", "\n") if isinstance(content, str) else str(content)
    
    console.print(Panel(
        Markdown(formatted_content),
        title=f"[bold green]Agent:[/bold green] {name}",
        border_style="green"
    ))
    
    
def pretty_print_json_contained_within_text(text):
    """Attempt to prettify JSON snippets within a larger text"""
    
    start = text.find('{')
    end = text.rfind('}')

    # If we can't find a matching '{' ... '}', just return as-is.
    if start == -1 or end == -1 or start > end:
        return text

    # 3. Extract the substring that might be JSON
    snippet = text[start:end+1]
    
    # need to get rid of the new lines to make it valid json for the next part
    snippet = snippet.replace("\n", "")

    # 4. Try to parse it as JSON
    try:
        parsed = json.loads(snippet)
        # 5. On success, prettify it with indentation
        pretty = json.dumps(parsed, indent=4)

        # Replace the original snippet with our prettified JSON
        text = text[:start] + pretty + text[end+1:]
    except json.JSONDecodeError:
        # If it doesn't parse as JSON, just leave the text alone
        pass

    return text    
    
def print_agent_multimodal_message(name, content):
    """Format agent messages nicely"""
    # typically content[0] will be the message and content[1] is the image
        
    formatted_content = pretty_print_json_contained_within_text(content[0])
    console.print(Panel(
        formatted_content,
        title=f"[bold green]Agent:[/bold green] {name}",
        border_style="green"
    ))

def custom_warning_formatter(message, category, filename, lineno, file=None, line=None):
    """Format warnings in a nicer way"""
    
    # the model mismatch warning is not useful and can be ignored
    if not "Resolved model mismatch" in str(message):    
        message=f"[yellow]Warning:[/yellow] {message}\n[dim]From: {filename}:{lineno}[/dim]"
        
        console.print(Panel(message,
            title="[bold yellow]Warning[/bold yellow]",
            border_style="yellow",
            width=100
        ))
    
    return ''

# Install the custom warning formatter
warnings.formatwarning = custom_warning_formatter