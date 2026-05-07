"""
SnowNinja REPL Shell — prompt_toolkit-powered interactive harness.

Renders a scrolling terminal REPL:
  - ASCII splash printed once to stdout on startup
  - Rich renders markdown/panels into the scrollback buffer
  - prompt_toolkit provides the sticky bottom input with autocomplete
  - Bottom toolbar shows connection / model / mode live
"""
import asyncio
import json
import sys
from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.spinner import Spinner
from rich.text import Text

from snowninja.session import session
from snowninja.core.config import save_config

console = Console()

VERSION = "0.2.0"

# ─────────────────────────────────────────────────────────────────────────────
# Snowflake Brand Palette
# ─────────────────────────────────────────────────────────────────────────────
SF_BLUE     = "#29B5E8"   # Snowflake primary blue
SF_BLUE_L   = "#56C9F2"   # Lighter blue
SF_BLUE_D   = "#1A82A8"   # Darker blue
SF_NAVY     = "#0D2233"   # Deep navy background
SF_NAV      = "#1B3B52"   # Toolbar background
SF_TEXT     = "#89A4B8"   # Secondary text
SF_YELLOW   = "#FFB81C"   # Accent/success
SF_YELLOW_L = "#FFD166"   # Lighter yellow
SF_WHITE    = "#FFFFFF"
SF_SNOW     = "#F4F7F9"   # Lightest background

# ─────────────────────────────────────────────────────────────────────────────
# ASCII splash
# ─────────────────────────────────────────────────────────────────────────────
NINJA_ASCII = r"""
        *       *       *
      *   *   *   *   *   *
        *   *   *   *   *
      *   *   *   *   *   *
    *   *   *       *   *   *
  *   *   *           *   *   *
    *   *               *   *
  *   *                   *   *
    *                       *
  *                           *

  ╔═╗╔╗╔╔═╗╦ ╦╔╗╔╦╔╗╔ ╦╔═╗
  ╚═╗║║║║ ║║║║║║║║║║║ ║╠═╣
  ╚═╝╝╚╝╚═╝╚╩╝╝╚╝╩╝╚╝╚╝╩ ╩
"""

# ─────────────────────────────────────────
# Slash commands with descriptions
# ─────────────────────────────────────────
SLASH_COMMANDS = {
    "/help":               "Show available commands",
    "/plan":               "Switch to Planner mode (reasoning model)",
    "/planner":            "Alias for /plan",
    "/implement":          "Switch to Implementer mode (coder model)",
    "/implementer":        "Alias for /implement",
    "/interview":          "Start guided requirements interview — /interview <goal>",
    "/go":                 "Finalize the interview and generate Requirements + Task List",
    "/explore":            "Switch to Explore mode (read-only data inspection)",
    "/explorer":           "Alias for /explore",
    "/operate":            "Switch to Operate mode (run pipelines, tasks, SQL)",
    "/govern":             "Switch to Govern mode (roles, grants, policies)",
    "/cost":               "Switch to Cost mode (warehouses, credits)",
    "/model planner ":     "Set the planner model  e.g. /model planner meta/llama-3.1-405b-instruct",
    "/model implementer ": "Set the implementer model  e.g. /model implementer qwen/qwen2.5-coder-32b-instruct",
    "/models":             "List available NIM model families",
    "/tools":              "List all loaded Snowflake action tools",
    "/skills":             "List skill guides (/skills <name> to view one)",
    "/tasks":              "Show task list  —  /tasks clear to wipe it",
    "/new":                "Fresh start — clears task list, requirements, interview & chat history",
    "/connection":         "Show current Snowflake connection status",
    "/scaffold":           "Scaffold a Snowflake project (pipeline, app, snowpark)",
    "/history":            "Show conversation history",
    "/clear":              "Clear conversation history only (keeps task list)",
    "/quit":               "Exit SnowNinja",
    "/exit":               "Exit SnowNinja",
}

MODES = {
    "plan":      ("planner",     "📐", SF_BLUE),
    "implement": ("implementer", "⚙️ ", SF_YELLOW),
    "explore":   ("implementer", "🔍", SF_BLUE_L),
    "operate":   ("implementer", "▶️ ", SF_YELLOW_L),
    "govern":    ("planner",     "🏛️ ", SF_BLUE_D),
    "cost":      ("planner",     "💰", SF_BLUE),
}

class SlashCompleter(Completer):
    """Inline dropdown completer triggered on '/'."""

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if not text.startswith("/"):
            return
        word = text.lstrip()
        for cmd, desc in SLASH_COMMANDS.items():
            if cmd.startswith(word):
                yield Completion(
                    cmd,
                    start_position=-len(word),
                    display=cmd,
                    display_meta=desc,
                )

PT_STYLE = Style.from_dict({
    "prompt":              f"bold",
    "bottom-toolbar":      f"bg:{SF_NAV} {SF_TEXT}",
    "bottom-toolbar.text": f"bg:{SF_NAV} {SF_TEXT}",
    "completion-menu.completion":              f"bg:{SF_NAVY} {SF_SNOW}",
    "completion-menu.completion.current":      f"bg:{SF_BLUE} {SF_WHITE} bold",
    "completion-menu.meta.completion":         f"bg:{SF_NAVY} {SF_TEXT}",
    "completion-menu.meta.completion.current": f"bg:{SF_BLUE} {SF_NAVY}",
})

def _print_splash() -> None:
    """Print the Snowflake-branded startup splash to stdout once."""
    config = session.config
    if config.snowflake_profile:
        conn_info = f"Profile: {config.snowflake_profile}"
    elif config.snowflake_url and config.snowflake_user:
        account = config.snowflake_url.split(".")[0]
        conn_info = f"{account} ({config.snowflake_user})"
    else:
        conn_info = "Not configured"

    impl    = config.implementer_model
    planner = config.planner_model

    logo_text = Text(NINJA_ASCII, style=f"bold {SF_BLUE}")
    console.print(logo_text)

    console.print(Rule(
        f"[bold]Snowflake Agent Harness[/]  [dim]v{VERSION}[/]",
        style=SF_BLUE,
    ))
    console.print()

    console.print(Panel(
        f"[bold {SF_YELLOW}]⬡  Connection:[/]  [white]{conn_info}[/]\n"
        f"[bold {SF_BLUE_L}]⚙  Implementer:[/] [white]{impl}[/]\n"
        f"[bold {SF_BLUE_D}]📐 Planner:[/]     [white]{planner}[/]",
        border_style=SF_NAVY,
        padding=(0, 2),
    ))

    tips = (
        f"  [bold {SF_YELLOW}]1.[/] Ask anything: [bold]show my warehouses[/] or [bold]create a medallion pipeline[/]\n"
        f"  [bold {SF_YELLOW}]2.[/] Switch modes:  [bold {SF_BLUE}]/plan[/]  [bold {SF_BLUE}]/implement[/]  [bold {SF_BLUE}]/explore[/]\n"
        f"  [bold {SF_YELLOW}]3.[/] Scaffold:      [bold {SF_BLUE}]/scaffold pipeline-project[/]  or  [bold {SF_BLUE}]/scaffold app-project[/]\n"
        f"  [bold {SF_YELLOW}]4.[/] Autocomplete:  type [bold {SF_BLUE}]/[/] — dropdown opens instantly"
    )
    console.print(Panel(
        tips,
        title=f"[bold {SF_BLUE}]Getting Started[/]",
        border_style=SF_NAV,
        padding=(0, 2),
    ))
    console.print()


class SnowNinjaShell:
    """The main prompt_toolkit REPL shell."""

    def __init__(self):
        self.mode = "implement"
        self.model_role = "implementer"
        self.mode_icon = "⚙️ "
        self.mode_color = SF_YELLOW
        self.history: list[dict] = []
        self._nim_client: Optional[object] = None
        self._loop = asyncio.new_event_loop()

    def _get_nim_client(self):
        if self._nim_client is None:
            from snowninja.llm.nim_client import NimClient
            self._nim_client = NimClient()
        return self._nim_client

    def _bottom_toolbar(self) -> HTML:
        config = session.config
        if config.snowflake_profile:
            conn = config.snowflake_profile
        elif config.snowflake_url and config.snowflake_user:
            conn = config.snowflake_url.split(".")[0]
        else:
            conn = "no-profile"

        model = (
            config.planner_model
            if self.model_role == "planner"
            else config.implementer_model
        )

        if session.interview_mode:
            mode_display = f"interview ({session.interview_turn_count}/5)"
            mode_color = SF_BLUE
            hint = "answer question or /go to finalize"
        else:
            mode_display = self.mode
            mode_color = SF_BLUE
            hint = "type / for commands"

        return HTML(
            f"  <b>❄</b> <style fg='{SF_YELLOW}'>{conn}</style>"
            f"  │  <b>mode:</b> <style fg='{mode_color}'>{mode_display}</style>"
            f"  │  <b>model:</b> <style fg='{SF_BLUE_L}'>{model.split('/')[-1]}</style>"
            f"  │  <style fg='{SF_TEXT}'>{hint}</style>  "
        )

    def _set_mode(self, mode: str) -> bool:
        if mode not in MODES:
            return False
        role, icon, color = MODES[mode]
        self.mode = mode
        self.model_role = role
        self.mode_icon = icon
        self.mode_color = color
        self._nim_client = None  # reset so role is re-applied
        return True

    # ─────────────────────────────────────
    # Slash command handlers
    # ─────────────────────────────────────

    def _cmd_help(self, _: list[str]) -> None:
        rows = "\n".join(
            f"  [bold {SF_BLUE}]{cmd:<30}[/] [dim {SF_TEXT}]{desc}[/]"
            for cmd, desc in SLASH_COMMANDS.items()
        )
        console.print(Panel(
            rows,
            title=f"[bold {SF_BLUE}]SnowNinja Commands[/]",
            border_style=SF_NAV,
            padding=(0, 2),
        ))

    def _cmd_mode(self, parts: list[str]) -> None:
        cmd = parts[0].lstrip("/")
        if cmd in MODES:
            mode = cmd
        elif len(parts) >= 2:
            mode = parts[1].lower()
        else:
            console.print(f"[red]Usage:[/] /<mode>  — one of: {', '.join(MODES.keys())}")
            return

        if self._set_mode(mode):
            console.print(Rule(f"[bold]Mode → {self.mode_icon} {mode.upper()}[/]", style=self.mode_color))
            if mode == "implement" and session.task_list:
                task_count = sum(
                    1 for line in session.task_list.splitlines()
                    if line.strip().startswith("- [ ]")
                )
                console.print(
                    f"\n  [bold {SF_YELLOW}]📋 Task list loaded[/] "
                    f"[dim]({task_count} task{'s' if task_count != 1 else ''} ready)[/]  "
                    f"[dim {SF_TEXT}]Type [bold {SF_YELLOW}]start[/] to begin, or ask about a specific task.[/]\n"
                )
        else:
            console.print(f"[red]Unknown mode:[/] {mode}  — choose from: {', '.join(MODES.keys())}")

    def _cmd_models(self, _: list[str]) -> None:
        planner_models = [
            ("meta/llama-4-maverick-17b-128e-instruct", "★ DEFAULT", "Llama 4 MoE · Maverick · Ultimate Reasoning"),
            ("mistralai/mistral-large-3-675b-instruct-2512", "FALLBACK", "675B Flagship · Deep Logic · Tool Calling ✓"),
            ("moonshotai/kimi-k2.6", "★ PREMIUM", "Kimi 2.6 · 11T MoE · Deep Context Reasoning"),
            ("google/gemma-4-31b-it", "FAST", "Gemma 4 · Ultra-Fast Planning"),
        ]
        implementer_models = [
            ("qwen/qwen3-coder-480b-a35b-instruct", "★ DEFAULT", "Qwen 3 480B · Best Agentic Coder on NIM"),
            ("deepseek-ai/deepseek-v4-pro", "STABLE", "DeepSeek V4 · High Fidelity Logic"),
            ("z-ai/glm-5.1", "NEW", "GLM 5.1 Flagship · Agentic Implementation"),
        ]

        def fmt_row(model_id: str, tag: str, desc: str, color: str) -> str:
            tag_str = f" [dim white][[/][bold white]{tag}[/][dim white]][/]" if tag else ""
            return f"  [{color}]{model_id}[/{color}]{tag_str}\n    [dim]{desc}[/]"

        planner_rows = "\n".join(fmt_row(m, t, d, "cyan") for m, t, d in planner_models)
        impl_rows    = "\n".join(fmt_row(m, t, d, "green") for m, t, d in implementer_models)

        table_content = (
            f"[bold white]📐 Planner Lane[/] [dim](reasoning · architecture · pipeline design)[/]\n\n"
            f"{planner_rows}\n\n"
            f"[bold white]⚙  Implementer Lane[/] [dim](SQL · Python UDFs · SnowSQL)[/]\n\n"
            f"{impl_rows}\n\n"
            f"[dim]Manual switch: [yellow]/model planner <id>[/]  or  [yellow]/model implementer <id>[/][/]"
        )
        console.print(Panel(
            table_content,
            title="[bold white]NIM Model Registry[/]",
            border_style="bright_blue",
            padding=(1, 2),
        ))

    def _cmd_connection(self, _: list[str]) -> None:
        from snowninja.actions.tools_core import tools
        prof = session.config.snowflake_profile or "Not set"
        console.print(Panel(
            f"[bold cyan]Profile:[/]  [white]{prof}[/]",
            title="[bold white]Connection[/]",
            border_style="cyan",
            padding=(0, 2),
        ))
        try:
            with console.status("[yellow]Checking auth...[/]"):
                user = tools.get_current_user()
            if user:
                console.print(f"  [green]✓[/] Authenticated as [bold]{user.get('USER')}[/]")
                console.print(f"  [dim]Role:[/] {user.get('ROLE')}")
                console.print(f"  [dim]Warehouse:[/] {user.get('WAREHOUSE')}")
            else:
                console.print(f"  [red]✗[/] Auth check failed (No results returned)")
        except Exception as e:
            console.print(f"  [red]✗[/] Auth check failed: {e}")

    def _cmd_tasks(self, parts: list[str]) -> None:
        subcommand = parts[1].lower() if len(parts) > 1 else ""

        if subcommand == "clear":
            from rich.prompt import Confirm
            if not session.task_list and not session.requirements:
                console.print("  [dim]Task list is already empty.[/]")
                return
            confirmed = Confirm.ask(
                f"  [bold {SF_BLUE}]Clear task list and requirements?[/] "
                f"[dim]({len(session.task_list.splitlines())} tasks)[/]"
            )
            if confirmed:
                session.task_list = ""
                session.requirements = ""
                session.reset_interview()
                console.print(f"  [bold {SF_YELLOW}]✓[/] [dim]Task list and requirements cleared.[/]")
        elif not session.task_list:
            console.print(
                f"  [dim]No task list yet. Use [yellow]/plan[/] or [yellow]/interview[/] to design something.[/]\n"
                f"  [dim]Tip: [yellow]/tasks clear[/] to wipe an existing task list.[/]"
            )
        else:
            req_panel = ""
            if session.requirements:
                req_panel = f"**Requirements**\n{session.requirements}\n\n---\n\n"
            console.print(Panel(
                Markdown(req_panel + "**Task List**\n" + session.task_list),
                title=(
                    f"[bold {SF_YELLOW}]📋 Plan[/] "
                    f"[dim]— /tasks clear to wipe — switch to [yellow]/implement[/] to execute[/]"
                ),
                border_style=SF_YELLOW,
                padding=(1, 2),
            ))

    def _cmd_interview(self, parts: list[str]) -> None:
        initial_goal = " ".join(parts[1:]).strip() if len(parts) > 1 else ""
        if not initial_goal:
            console.print(
                f"  [bold {SF_YELLOW}]Usage:[/] [white]/interview <your goal>[/]\n"
                f"  [dim]Example: /interview I want to build a Cortex document processor[/]"
            )
            return

        client = self._get_nim_client()
        client.reset_interview()
        session.reset_interview()
        session.interview_mode = True

        console.print()
        console.print(Panel(
            f"[bold white]{initial_goal}[/]\n\n"
            f"[dim]I'll ask a few focused questions to shape the requirements.\n"
            f"Answer each one, then type [bold yellow]/go[/] when you're ready to generate the Task List.[/]",
            title=f"[bold {SF_BLUE}]🎙️  Requirements Interview[/]",
            border_style=SF_BLUE,
            padding=(1, 2),
        ))
        console.print()

        self._run_interview(initial_goal, force_finalize=False)

    def _cmd_go(self, _: list[str]) -> None:
        if not session.interview_mode:
            console.print(f"  [dim]No active interview. Start one with [yellow]/interview <goal>[/][/]")
            return
        self._run_interview("Please finalize now.", force_finalize=True)

    def _run_interview(self, user_message: str, force_finalize: bool = False) -> None:
        client = self._get_nim_client()
        model_short = session.config.planner_model.split("/")[-1]

        if not force_finalize:
            console.print(f"[bold {SF_BLUE}]❯[/] [white]{user_message}[/]")
            console.print()

        async def _run():
            response_text = ""
            event_type_final = "text"

            spinner = Spinner(
                "dots",
                text=f"  🎙️  Analyst thinking… ({model_short})",
                style=f"bold {SF_BLUE}",
            )

            with Live(spinner, console=console, refresh_per_second=12, transient=True):
                async for ev_type, data in client.interview_chat(
                    user_message, force_finalize=force_finalize
                ):
                    if ev_type == "error":
                        console.print(Panel(f"[red]{data}[/]", title="[red]Error[/]", border_style="red"))
                        return
                    response_text = data
                    event_type_final = ev_type

            console.print()

            if event_type_final == "interview_complete":
                session.interview_mode = False
                req_text = ""
                task_text = ""

                if "## Requirements" in response_text and "## Task List" in response_text:
                    req_section = response_text.split("## Requirements", 1)[1]
                    req_text = req_section.split("## Task List", 1)[0].strip()
                    task_text = req_section.split("## Task List", 1)[1].strip()

                session.requirements = req_text
                session.task_list = task_text

                console.print(Panel(
                    Markdown(response_text),
                    title=f"[bold {SF_YELLOW}]📋 Requirements & Task List[/]",
                    border_style=SF_YELLOW,
                    padding=(1, 2),
                ))
                console.print()
                console.print(
                    f"  [bold {SF_YELLOW}]✓ Task list saved.[/] "
                    f"[dim]Switch to [yellow]/implement[/] — the Implementer will pick it up automatically.[/]"
                )

            elif event_type_final == "interview_ready":
                console.print(Markdown(response_text))
                console.print()
                console.print(
                    f"  [dim {SF_TEXT}]Type [bold {SF_YELLOW}]/go[/] to generate the task list, "
                    f"or keep answering questions.[/]"
                )
                session.interview_turn_count += 1

            else:
                console.print(Markdown(response_text))
                session.interview_turn_count += 1
                if session.interview_turn_count >= 5:
                    console.print(
                        f"\n  [dim {SF_TEXT}](5 questions reached — "
                        f"type [bold {SF_YELLOW}]/go[/] to generate the task list)[/]"
                    )

        self._loop.run_until_complete(_run())
        console.print()

    def _cmd_skills(self, parts: list[str]) -> None:
        from snowninja.skills.router import skill_router
        from pathlib import Path
        import re

        skill_arg = parts[1].lower() if len(parts) > 1 else None

        if skill_arg:
            content = skill_router.load_skill(skill_arg)
            if content:
                console.print(Panel(
                    Markdown(content),
                    title=f"[bold {SF_YELLOW}]📖 Skill: {skill_arg}[/]",
                    border_style=SF_YELLOW,
                    padding=(1, 2),
                ))
            else:
                console.print(f"  [red]Skill not found:[/] {skill_arg}")
                console.print("  [dim]Use [yellow]/skills[/] to list available skills.[/]")
        else:
            skills_dir = Path(__file__).parent.parent / "skills"
            lines = []
            for f in sorted(skills_dir.glob("*.md")):
                text = f.read_text(encoding="utf-8")
                m = re.search(r'description:\s*["\']?(.+?)["\']?\s*\n', text)
                desc = m.group(1)[:90] if m else ""
                lines.append(f"  [bold green]{f.stem:<35}[/] [dim]{desc}[/]")
            console.print(Panel(
                "\n".join(lines),
                title=f"[bold white]Snowflake Skill Guides ({len(lines)} loaded)[/] "
                      f"[dim]— /skills <name> to view full content[/]",
                border_style="green",
                padding=(0, 2),
            ))

    def _cmd_tools(self, _: list[str]) -> None:
        from snowninja.llm.nim_client import SNOWFLAKE_TOOLS
        tools_list = "\n".join(
            f"  [bold green]{t['function']['name']:<35}[/] [dim]{t['function']['description']}[/]"
            for t in SNOWFLAKE_TOOLS
        )
        console.print(Panel(tools_list, title=f"[bold white]Snowflake Action Tools ({len(SNOWFLAKE_TOOLS)} loaded)[/]", border_style="green", padding=(0, 2)))

    def _cmd_set_model(self, parts: list[str]) -> None:
        if len(parts) < 3:
            console.print("[red]Usage:[/] /model planner <name>  or  /model implementer <name>")
            return
        lane, model_name = parts[1].lower(), parts[2]
        if lane in ("planner", "plan"):
            session.config.planner_model = model_name
            save_config(session.config)
            console.print(f"  [green]✓[/] Planner model set to [bold]{model_name}[/]")
        elif lane in ("implementer", "implement"):
            session.config.implementer_model = model_name
            save_config(session.config)
            console.print(f"  [green]✓[/] Implementer model set to [bold]{model_name}[/]")
        else:
            console.print(f"[red]Unknown lane:[/] {lane}. Use [yellow]planner[/] or [yellow]implementer[/].")
        self._nim_client = None

    def _cmd_clear(self, _: list[str]) -> None:
        self.history = []
        if self._nim_client:
            self._nim_client.reset_history()
        console.print(Rule("[dim]Conversation history cleared (task list preserved)[/]", style="dim"))

    def _cmd_new(self, _: list[str]) -> None:
        from rich.prompt import Confirm
        has_state = bool(session.task_list or session.requirements or session.interview_mode)
        has_history = bool(self.history)
        if not has_state and not has_history:
            console.print("  [dim]Nothing to clear — already a clean slate.[/]")
            return

        parts = []
        if session.task_list:
            parts.append(f"{len(session.task_list.splitlines())} task(s)")
        if session.requirements:
            parts.append("requirements")
        if has_history:
            parts.append(f"{len(self.history)} message(s)")
        summary = ", ".join(parts)

        confirmed = Confirm.ask(
            f"  [bold {SF_BLUE}]Start fresh?[/] [dim]This will clear: {summary}[/]"
        )
        if not confirmed:
            console.print("  [dim]Cancelled.[/]")
            return

        session.task_list = ""
        session.requirements = ""
        session.reset_interview()
        self.history = []
        if self._nim_client:
            self._nim_client.reset_history()

        console.print()
        console.print(Rule(
            f"[bold {SF_BLUE}]🥷  Fresh start[/]  [dim]Task list, requirements, and conversation cleared.[/]",
            style=SF_BLUE,
        ))
        console.print()

    def _cmd_history(self, _: list[str]) -> None:
        if not self.history:
            console.print("[dim]No history yet.[/]")
            return
        for i, msg in enumerate(self.history):
            role = "[bold cyan]You[/]" if msg["role"] == "user" else "[bold green]SnowNinja[/]"
            console.print(f"[dim]{i+1}.[/] {role}: {msg['content'][:200]}...")

    def _cmd_scaffold(self, parts: list[str]) -> None:
        from snowninja.scaffold.engine import ScaffoldEngine
        template = parts[1] if len(parts) > 1 else None
        engine = ScaffoldEngine()
        engine.run(template)

    def _dispatch_slash(self, raw: str) -> bool:
        parts = raw.strip().split()
        cmd = parts[0].lower()

        if cmd == "/help":                   self._cmd_help(parts); return True
        if cmd in MODES:                     self._cmd_mode(parts); return True
        if cmd in ("/plan", "/planner",
                   "/implement", "/implementer",
                   "/explore", "/explorer",
                   "/operate", "/govern", "/cost"): self._cmd_mode(parts); return True
        if cmd == "/models":                 self._cmd_models(parts); return True
        if cmd == "/tasks":                  self._cmd_tasks(parts); return True
        if cmd == "/skills":                 self._cmd_skills(parts); return True
        if cmd == "/interview":              self._cmd_interview(parts); return True
        if cmd == "/go":                     self._cmd_go(parts); return True
        if cmd == "/new":                    self._cmd_new(parts); return True
        if cmd == "/connection":             self._cmd_connection(parts); return True
        if cmd == "/tools":                  self._cmd_tools(parts); return True
        if cmd == "/model":                  self._cmd_set_model(parts); return True
        if cmd == "/clear":                  self._cmd_clear(parts); return True
        if cmd == "/history":                self._cmd_history(parts); return True
        if cmd == "/scaffold":               self._cmd_scaffold(parts); return True
        if cmd in ("/quit", "/exit"):
            console.print("\n[dim]Goodbye. 🥷[/]\n")
            raise SystemExit(0)
        return False

    # ─────────────────────────────────────
    # Agent interaction
    # ─────────────────────────────────────

    def _run_agent(self, user_input: str) -> None:
        from snowninja.llm.nim_client import ModelRole

        client = self._get_nim_client()
        role = ModelRole.PLANNER if self.model_role == "planner" else ModelRole.IMPLEMENTER

        model_short = (
            session.config.planner_model if self.model_role == "planner"
            else session.config.implementer_model
        ).split("/")[-1]

        console.print(f"\n[bold {SF_BLUE}]❯[/] [white]{user_input}[/]")
        console.print()

        async def _run():
            nonlocal model_short
            response_text = ""
            errors: list[str] = []
            last_tool: str = "tool"

            spinner = Spinner("dots", text=f"  Calling {model_short}…", style=f"bold {SF_BLUE}")

            with Live(spinner, console=console, refresh_per_second=12, transient=True):
                async for event_type, data in client.agent_chat(user_input, role=role):

                    if event_type == "tool_call":
                        fn_name, fn_args = data
                        last_tool = fn_name
                        args_str = ", ".join(
                            f'{k}="{v}"' for k, v in fn_args.items()
                        ) if fn_args else ""
                        spinner.text = f"  🔧 {fn_name}({args_str})…"

                    elif event_type == "tool_result":
                        try:
                            parsed = json.loads(data)
                            if isinstance(parsed, list):
                                summary = f"{len(parsed)} item{'s' if len(parsed) != 1 else ''}"
                            elif isinstance(parsed, dict) and "error" in parsed:
                                summary = f"⚠ {str(parsed['error'])[:60]}"
                            else:
                                summary = "ok"
                        except Exception:
                            summary = "done"
                        console.print(
                            f"  [bold {SF_YELLOW}]🔧[/] [white]{last_tool}[/] "
                            f"[dim {SF_TEXT}]→ {summary}[/]",
                            highlight=False,
                        )
                        spinner.text = f"  Calling {model_short}…"

                    elif event_type == "skill_match":
                        skill_names = ", ".join(data)
                        spinner.text = f"  📚 Skills: {skill_names} | Calling {model_short}…"

                    elif event_type == "model_switch":
                        new_short = data.split("/")[-1]
                        model_short = new_short
                        spinner.text = f"  ⚡ Switching to {new_short}…"
                        console.print(
                            f"  [bold {SF_YELLOW}]⚡ Fallback:[/] [dim]overloaded → switching to[/] "
                            f"[bold {SF_BLUE_L}]{data}[/]"
                        )

                    elif event_type == "text":
                        response_text = data
                        spinner.text = "  Composing response…"

                    elif event_type == "error":
                        errors.append(data)

            for err in errors:
                console.print(Panel(f"[red]{err}[/]", title="[red]Error[/]", border_style="red"))

            if response_text:
                console.print()
                console.print(Markdown(response_text))

                if self.model_role == "planner" and "## Task List" in response_text:
                    try:
                        task_section = response_text.split("## Task List", 1)[1].strip()
                        session.task_list = task_section
                        console.print(
                            f"  [bold {SF_YELLOW}]📋 Task list saved[/] "
                            f"[dim]— switch to [yellow]/implement[/] and the Implementer will pick it up[/]"
                        )
                    except IndexError:
                        pass # Safety check in case splitting fails

            self.history.append({"role": "user", "content": user_input})
            self.history.append({"role": "assistant", "content": response_text})

        try:
            self._loop.run_until_complete(_run())
        except Exception as exc:
            import os, traceback
            console.print(Panel(
                f"[red]{type(exc).__name__}:[/] {exc}",
                title="[bold red]⚠ Agent Error[/]",
                border_style="red",
            ))
            if os.environ.get("SNOWNINJA_DEBUG"):
                traceback.print_exc()
        console.print()

    # ─────────────────────────────────────
    # Main REPL loop
    # ─────────────────────────────────────

    def run(self) -> None:
        _print_splash()

        kb = KeyBindings()

        @kb.add("c-c")
        def _exit(event):
            console.print("\n[dim]Goodbye. 🥷[/]\n")
            event.app.exit()

        @kb.add("/")
        def _slash_complete(event):
            event.current_buffer.insert_text("/")
            event.current_buffer.start_completion(select_first=False)

        session_pt = PromptSession(
            completer=SlashCompleter(),
            auto_suggest=AutoSuggestFromHistory(),
            style=PT_STYLE,
            key_bindings=kb,
            bottom_toolbar=self._bottom_toolbar,
            complete_while_typing=True,
            mouse_support=False,
            enable_history_search=True,
        )

        while True:
            try:
                if session.interview_mode:
                    placeholder_text = f"<style fg='{SF_TEXT}'>Answer the question above, or type /go to generate task list…</style>"
                    prompt_prefix = HTML(f"<style fg='{SF_BLUE}' bold='true'>🎙️ </style>")
                else:
                    placeholder_text = f"<style fg='{SF_TEXT}'>Ask anything, or type / for commands…</style>"
                    prompt_prefix = HTML(f"<style fg='{SF_BLUE}' bold='true'>❯ </style>")

                user_input = session_pt.prompt(
                    prompt_prefix,
                    placeholder=HTML(placeholder_text),
                ).strip()
            except (KeyboardInterrupt, EOFError):
                console.print(f"\n[dim {SF_TEXT}]Goodbye. 🥷[/]\n")
                break

            if not user_input:
                continue

            if user_input.startswith("/"):
                handled = self._dispatch_slash(user_input)
                if not handled:
                    console.print(f"[{SF_BLUE}]Unknown command:[/] {user_input}  — type [bold {SF_YELLOW}]/help[/] for a list.")
                continue

            try:
                if session.interview_mode:
                    self._run_interview(user_input, force_finalize=False)
                else:
                    self._run_agent(user_input)
            except KeyboardInterrupt:
                console.print(f"\n[{SF_YELLOW}]Interrupted.[/]")
            except Exception as exc:
                import os, traceback
                console.print(Panel(
                    f"[red]{type(exc).__name__}:[/] {exc}\n\n"
                    f"[dim]Set [bold]SNOWNINJA_DEBUG=1[/] and retry for full traceback.[/]",
                    title="[bold red]⚠ Unexpected Error[/]",
                    border_style="red",
                ))
                if os.environ.get("SNOWNINJA_DEBUG"):
                    traceback.print_exc()

def main():
    try:
        shell = SnowNinjaShell()
        shell.run()
    except Exception as e:
        import traceback
        console.print(f"[red]Fatal Error:[/] {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
