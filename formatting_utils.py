import ast
import json
import re
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
import warnings

console = Console()

# Global dictionary to hold agent color mappings
_AGENT_COLORS = {}

def set_agent_colors(color_map: dict):
    """Set the color mapping for agents dynamically."""
    global _AGENT_COLORS
    _AGENT_COLORS = color_map
    
def get_colored_agent_name(name):
    color = _AGENT_COLORS.get(name, "green")  # Default to green if agent not found
    return f"[{color}]{name}[/{color}]"

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
        return repr(args_obj)

async def process_message(message, source: str):
    """Process and format messages from the agent stream."""    
    try:
        if type(message).__name__ == 'TextMessage' and hasattr(message, 'content'):
            source = message.source if hasattr(message, 'source') else "Unknown"
            print_agent_message(source, message.content)
        elif type(message).__name__ == 'MultiModalMessage' and hasattr(message, 'content'):
            print_agent_multimodal_message(source, message.content)
        elif type(message).__name__ == 'ToolCallRequestEvent' and hasattr(message, 'content'):
            agent_color = _AGENT_COLORS.get(source, "yellow")
            if isinstance(message.content, list):
                for call in message.content:
                    if type(call).__name__ == 'FunctionCall':
                        name = call.name
                        args_str = format_function_arguments(call.arguments)
                        tool_use_message = f"[bold {agent_color}]Function Call:[/bold {agent_color}] {name}({args_str})"
                        console.print(Panel(
                            tool_use_message,
                            title=f"[bold {agent_color}]Tool Use Function Call From {source}[/bold {agent_color}]",
                            border_style=agent_color
                        ))        
        elif type(message).__name__ == 'ToolCallExecutionEvent' and hasattr(message, 'content'):
            pass  # Skipping as per original behavior
            # if isinstance(message.content, list):
            #     for result in message.content:
            #         if type(result).__name__ == 'FunctionExecutionResult':
            #             print_tool_result(result.content, type(result).__name__, message.source, result.call_id, result.is_error)
            #         else:
            #             console.print(f"[red]Unexpected content format: {result.content}[/red]")
            # else:
            #     console.print(f"[red]Unexpected content format: type=={type(message.content).__name__} - content: {message.content}[/red]")
                        
        elif type(message).__name__ == 'ToolCallSummaryMessage' and hasattr(message, 'content'):
            agent_color = _AGENT_COLORS.get(source, "yellow")
            lines = [line.strip() for line in message.content.splitlines() if line.strip()]
            literal = f"[{','.join(lines)}]"
            python_obj = ast.literal_eval(literal)
            json_str = json.dumps(python_obj, indent=4)
            print_tool_result(json_str, "ToolCallSummaryMessage", source, "", is_error=False)
        else:
            console.print(str(message))
    except Exception as e:
        console.print(f"[bold red]Error processing message:[/bold red] {str(e)}")

def format_json(data, title=None):
    """Pretty print JSON data with syntax highlighting."""
    try:
        python_obj = ast.literal_eval(data)
        json_str = json.dumps(python_obj, indent=4)
        json_str = re.sub(r'(?i)<br\s*/?>', '\n', json_str)
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
        if title:
            return Panel(syntax, title=title, border_style="orange3")
        return syntax
    except:
        return data

def print_section(title, subtitle=None):
    """Print a section header with optional subtitle."""
    console.print("\n")
    console.rule(f"[bold orange3]{title}[/bold orange3]", style="orange3")
    if subtitle:
        console.print(f"[dim]{subtitle}[/dim]", justify="center")
    console.print("\n")

def print_tool_result(result, message_type: str, agent_name: str, call_id: str, is_error: bool = False):
    """Format tool results nicely."""
    style = "red" if is_error else _AGENT_COLORS.get(agent_name, "green")
    panel_title = f"[bold {style}]{message_type} from {agent_name}[/bold {style}]"
    try:
        if isinstance(result, str):
            try:
                content = format_json(result)
                console.print(Panel(content, title=panel_title, border_style=style))
            except:
                console.print(Panel(result, title=panel_title, border_style=style))
        else:
            console.print(Panel(format_json(result), title=panel_title, border_style=style))
    except:
        console.print(Panel(str(result), title=panel_title, border_style=style))

def print_agent_message(name, content):
    color = _AGENT_COLORS.get(name, "green")
    formatted_content = content.replace("\\n", "\n") if isinstance(content, str) else str(content)
    console.print(Panel(
        Markdown(formatted_content),
        title=f"[bold {color}]Agent:[/bold {color}] {name}",
        border_style=color
    ))

def pretty_print_json_contained_within_text(text):
    """Attempt to prettify JSON snippets within a larger text."""
    start = text.find('{')
    end = text.rfind('}')
    if start == -1 or end == -1 or start > end:
        return text
    snippet = text[start:end+1].replace("\n", "")
    try:
        parsed = json.loads(snippet)
        pretty = json.dumps(parsed, indent=4)
        text = text[:start] + pretty + text[end+1:]
    except json.JSONDecodeError:
        pass
    return text

def print_agent_multimodal_message(name, content):
    """Format multimodal agent messages with dynamic agent-specific colors."""
    color = _AGENT_COLORS.get(name, "green")
    formatted_content = pretty_print_json_contained_within_text(content[0])
    console.print(Panel(
        formatted_content,
        title=f"[bold {color}]Agent:[/bold {color}] {name}",
        border_style=color
    ))

def custom_warning_formatter(message, category, filename, lineno, file=None, line=None):
    """Format warnings in a nicer way."""
    if "Resolved model mismatch" not in str(message):
        message = f"[yellow]Warning:[/yellow] {message}\n[dim]From: {filename}:{lineno}[/dim]"
        console.print(Panel(
            message,
            title="[bold yellow]Warning[/bold yellow]",
            border_style="yellow",
            width=100
        ))
    return ''

warnings.formatwarning = custom_warning_formatter