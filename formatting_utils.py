# formatting_utils.py
import json
import warnings
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.table import Table
from rich.box import ROUNDED
from rich.rule import Rule

# Create a singleton console instance
console = Console()

def format_json(data, title=None):
    """Pretty print JSON data with syntax highlighting"""
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except:
            # If it's not valid JSON, return as is
            return data
    
    if isinstance(data, (dict, list)):
        json_str = json.dumps(data, indent=4)
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
        if title:
            return Panel(syntax, title=title, border_style="blue")
        return syntax
    return str(data)

def print_section(title, subtitle=None):
    """Print a section header with optional subtitle"""
    console.print("\n")
    console.rule(f"[bold blue]{title}[/bold blue]", style="blue")
    
    if subtitle:
        console.print(f"[dim]{subtitle}[/dim]", justify="center")
    console.print("\n")

def print_tool_call(name, arguments):
    """Format tool calls nicely"""
    try:
        args = json.loads(arguments) if isinstance(arguments, str) else arguments
        console.print(Panel(
            format_json(args),
            title=f"[bold yellow]Function Call:[/bold yellow] {name}",
            border_style="yellow"
        ))
    except:
        console.print(Panel(
            str(arguments),
            title=f"[bold yellow]Function Call:[/bold yellow] {name}",
            border_style="yellow"
        ))

def print_tool_result(result, call_id, is_error=False):
    """Format tool results nicely"""
    style = "red" if is_error else "green"
    title = f"[bold {style}]Function Result:[/bold {style}] {call_id[:10]}..."
    
    try:
        if isinstance(result, str):
            try:
                content = json.loads(result)
                console.print(Panel(
                    format_json(content),
                    title=title,
                    border_style=style
                ))
            except:
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

def handle_warning(message="Warning message"):
    """Format warning messages nicely"""
    console.print(Panel(
        f"[yellow]{message}[/yellow]",
        title="[bold yellow]Warning[/bold yellow]",
        border_style="yellow",
        width=100
    ))

# Fixed warning formatter with correct number of parameters
def custom_warning_formatter(message, category, filename, lineno, file=None, line=None):
    """Format warnings in a nicer way"""
    return f"[yellow]Warning:[/yellow] {message}\n[dim]From: {filename}:{lineno}[/dim]"

# Install the custom warning formatter
warnings.formatwarning = custom_warning_formatter