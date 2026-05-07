import typer
from rich.console import Console
from rich.panel import Panel

from .session import session
from .core.connections import test_connection, list_profiles
from .core.config import save_config

app = typer.Typer(
    name="snowninja",
    help="SnowNinja — Personal Snowflake Agent Harness",
    add_completion=False,
)

console = Console()

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    SnowNinja CLI - Bespoke Agent Harness for Snowflake
    """
    if ctx.invoked_subcommand is None:
        if not session.is_configured:
            console.print("[yellow]SnowNinja is not fully configured. Run 'snowninja setup' first.[/yellow]")
            raise typer.Exit(code=1)
            
        console.print(Panel.fit("[bold blue]❄️  SnowNinja Agent Harness ❄️[/bold blue]\nType [bold green]/help[/bold green] for commands.", border_style="blue"))
        # In later phases, we will launch the REPL here
        console.print("[dim]REPL shell will be implemented in Phase 5...[/dim]")

@app.command()
def setup():
    """Run the first-time setup wizard for SnowNinja."""
    console.print("[bold blue]Welcome to SnowNinja Setup[/bold blue]")
    
    # Simple wizard for now
    nvidia_pat = typer.prompt("Enter your NVIDIA NIM API Key (PAT)", default=session.config.nvidia_pat, hide_input=True)
    session.config.nvidia_pat = nvidia_pat
    
    profiles = list_profiles()
    if profiles:
        console.print(f"Found Snowflake profiles in ~/.snowflake/connections.toml: {', '.join(profiles)}")
        profile = typer.prompt("Which profile would you like to use?", default=session.config.snowflake_profile or profiles[0])
        session.config.snowflake_profile = profile
    else:
        console.print("[yellow]No ~/.snowflake/connections.toml found. We will use the fallback config for now.[/yellow]")
        
    save_config(session.config)
    console.print("[green]Configuration saved![/green]")

@app.command()
def doctor():
    """Verify authentication and system readiness."""
    console.print("[bold]Running SnowNinja Diagnostics...[/bold]")
    
    # 1. Check Config
    if session.is_configured:
        console.print("✅ Config: [green]OK[/green] (NVIDIA PAT found)")
    else:
        console.print("❌ Config: [red]Missing NVIDIA PAT[/red]")
        
    # 2. Check Snowflake Connection
    console.print("🔄 Testing Snowflake connection...")
    result = test_connection()
    
    if result.get("status") == "success":
        console.print(f"✅ Snowflake: [green]Connected as {result['user']} to {result['account']}[/green]")
        console.print(f"   Role: {result['role']} | Warehouse: {result['warehouse']}")
    else:
        console.print(f"❌ Snowflake: [red]Connection failed[/red]")
        console.print(f"   Error: {result.get('error')}")

if __name__ == "__main__":
    app()
