"""
SnowNinja CLI entry point.
"""
import sys
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from snowninja.core.config import SnowNinjaConfig, save_config, load_config
from snowninja.session import session

app = typer.Typer(
    name="snowninja",
    help="SnowNinja CLI — Snowflake Agent Harness",
    add_completion=True,
    invoke_without_command=True,
    no_args_is_help=False,
)

console = Console()


@app.callback()
def main(ctx: typer.Context):
    """
    Launch the SnowNinja interactive shell.
    Run without arguments to launch the REPL.
    """
    if ctx.invoked_subcommand is None:
        if not session.is_configured:
            console.print(Panel(
                "[bold red]SnowNinja is not fully configured.[/]\n\n"
                "Run [bold cyan]snowninja setup[/] to configure your environment.",
                border_style="red"
            ))
            raise typer.Exit(1)

        try:
            from snowninja.repl.shell import SnowNinjaShell
            shell = SnowNinjaShell()
            shell.run()
        except Exception as e:
            console.print(f"[red]Fatal Error launching shell:[/] {e}")
            sys.exit(1)


@app.command()
def setup():
    """Guided setup — configure NIM API key, Snowflake auth, and models."""
    console.print(Panel.fit(
        "[bold cyan]Welcome to SnowNinja Setup[/]\n"
        "[dim]Let's configure your Snowflake Agent Harness.[/]",
        border_style="cyan"
    ))

    # 1. NVIDIA NIM PAT
    nvidia_pat = Prompt.ask(
        "\n[bold yellow]NVIDIA API Key[/] [dim](starts with nvapi-)[/]",
        password=True
    )

    # 2. Snowflake Connection Strategy
    console.print("\n[bold cyan]Snowflake Connection[/]")
    strategy = Prompt.ask(
        "Use local ~/.snowflake/connections.toml profile or explicit PAT?",
        choices=["profile", "pat"],
        default="profile"
    )

    profile_name = ""
    snowflake_pat = ""

    if strategy == "profile":
        profile_name = Prompt.ask(
            "  [bold yellow]Profile Name[/] [dim](e.g., default)[/]",
            default="default"
        )
    else:
        snowflake_pat = Prompt.ask(
            "  [bold yellow]Snowflake OAuth Token[/]",
            password=True
        )

    # 3. Model Lanes
    console.print("\n[bold cyan]Agent Model Selection[/]")
    planner_model = Prompt.ask(
        "  [bold yellow]Planner Model[/]",
        default="meta/llama-3.1-405b-instruct"
    )
    implementer_model = Prompt.ask(
        "  [bold yellow]Implementer Model[/]",
        default="qwen/qwen2.5-coder-32b-instruct"
    )

    config = SnowNinjaConfig(
        nvidia_pat=nvidia_pat,
        snowflake_profile=profile_name,
        snowflake_pat=snowflake_pat,
        planner_model=planner_model,
        implementer_model=implementer_model,
    )
    save_config(config)
    session.reload_config()

    console.print(Panel(
        "[green]✓ Configuration saved to ~/.snowninja/config.yaml[/]\n"
        "[dim]Run [bold]snowninja[/] to launch the TUI.[/]",
        title="Setup Complete",
        border_style="green"
    ))


@app.command()
def doctor():
    """Run diagnostics to verify connection to Snowflake and NVIDIA NIM."""
    if not session.is_configured:
        console.print("[red]Not configured. Run `snowninja setup` first.[/]")
        raise typer.Exit(1)

    console.print(Panel("[bold cyan]SnowNinja System Diagnostics[/]", border_style="cyan"))

    # 1. Config Check
    console.print("[bold]1. Local Configuration[/]")
    console.print("  [green]✓[/] config.yaml is fully populated")

    # 2. NVIDIA NIM Check
    console.print("\n[bold]2. NVIDIA NIM API[/]")
    try:
        from openai import OpenAI
        client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=session.config.nvidia_pat
        )
        with console.status("[yellow]Pinging NIM API...[/]"):
            client.models.list()
        console.print("  [green]✓[/] Successfully connected to integrate.api.nvidia.com")
    except Exception as e:
        console.print(f"  [red]✗[/] NIM API connection failed: {e}")

    # 3. Snowflake Connection Check
    console.print("\n[bold]3. Snowflake Connection[/]")
    try:
        from snowninja.actions.tools_core import tools
        with console.status("[yellow]Connecting to Snowflake...[/]"):
            user = tools.get_current_user()
            
        if user and user.get("USER"):
            console.print(f"  [green]✓[/] Authenticated as [bold]{user['USER']}[/]")
            if user.get("ROLE"):
                console.print(f"  [green]✓[/] Current Role: {user['ROLE']}")
            if user.get("WAREHOUSE"):
                console.print(f"  [green]✓[/] Current Warehouse: {user['WAREHOUSE']}")
            else:
                console.print("  [yellow]⚠[/] No active warehouse")
        else:
            console.print("  [red]✗[/] Auth check returned no user context")
            
    except Exception as e:
        console.print(f"  [red]✗[/] Snowflake connection failed: {e}")

    console.print("\n[dim]Diagnostics complete.[/]")


if __name__ == "__main__":
    app()
