from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from typing import Optional

# Snowflake Brand Palette
SF_BLUE = "#29B5E8"
SF_NAVY = "#0D2233"
SF_GRAY = "#F1F5F9"
SF_WHITE = "#FFFFFF"

# Semantic Colors
SF_SUCCESS = "#22C55E"
SF_WARNING = "#F59E0B"
SF_ERROR = "#EF4444"

console = Console()

def print_agent_message(content: str, title: str = "SnowNinja Agent", style: str = SF_BLUE):
    """Prints a styled message from the agent."""
    panel = Panel(
        Markdown(content),
        title=f"[{style}]{title}[/{style}]",
        border_style=style,
        padding=(1, 2)
    )
    console.print(panel)

def print_system_message(content: str, is_error: bool = False):
    """Prints a system notification or error."""
    color = SF_ERROR if is_error else SF_WARNING
    icon = "❌" if is_error else "⚠️"
    console.print(f"[{color}]{icon} {content}[/{color}]")

def print_welcome_splash():
    """Prints the SnowNinja ASCII splash screen."""
    splash = f"""[{SF_BLUE}]
   _____                      _   _ _       _       
  / ____|                    | \\ | (_)     (_)      
 | (___  _ __   _____      __|  \\| |_ _ __  _  __ _ 
  \\___ \\| '_ \\ / _ \\ \\ /\\ / / . ` | | '_ \\| |/ _` |
  ____) | | | | (_) \\ V  V /| |\\  | | | | | | (_| |
 |_____/|_| |_|\\___/ \\_/\\_/ |_| \\_|_|_| |_| |\\__,_|
                                         _/ |       
                                        |__/        
[/{SF_BLUE}]
[{SF_GRAY}]A Bespoke Agent Harness for Snowflake Architecture[/{SF_GRAY}]
"""
    console.print(splash)
    console.print(f"Type [{SF_SUCCESS}]/help[/{SF_SUCCESS}] to see available commands.")
