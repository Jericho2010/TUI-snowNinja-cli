import asyncio
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style

from snowninja.session import session
from snowninja.tui.panels import print_agent_message, print_system_message, print_welcome_splash, console
from snowninja.llm.models import ModelRole
from snowninja.llm.nim_client import NimClient
from snowninja.skills.router import SkillRouter
from snowninja.core.connections import list_profiles, test_connection

# Slash Commands Mapping
SLASH_COMMANDS = {
    "/help": "Show available commands",
    "/quit": "Exit the REPL",
    "/clear": "Clear the terminal screen",
    "/plan": "Switch to Planner mode",
    "/implement": "Switch to Implementer mode",
    "/explore": "Switch to Explore mode",
    "/operate": "Switch to Operate mode",
    "/govern": "Switch to Governance mode",
    "/cortex": "Switch to Cortex AI mode",
    "/interview": "Start a requirements gathering interview",
    "/go": "End interview and proceed with current requirements",
    "/tasks": "List all current tasks in the session",
    "/task add": "Add a manual task",
    "/task clear": "Clear all tasks",
    "/skills": "List available Snowflake skill guides",
    "/tools": "List available Snowflake tools",
    "/profiles": "List local Snowflake connection profiles",
    "/profile": "Switch active Snowflake profile (/profile <name>)",
    "/connection": "Test current Snowflake connection",
    "/model": "Switch the active model (/model planner|implementer <model_name>)",
    "/models": "List current model assignments",
    "/scaffold": "Generate project scaffold (/scaffold dbt|streamlit|snowpark <name>)",
}

# Map modes to ModelRole (for test requirement: "Every mode maps to 'planner' or 'implementer'")
MODES = {
    "plan": ModelRole.PLANNER,
    "implement": ModelRole.IMPLEMENTER,
    "explore": ModelRole.IMPLEMENTER,
    "operate": ModelRole.IMPLEMENTER,
    "govern": ModelRole.PLANNER,
    "cortex": ModelRole.IMPLEMENTER
}

import re

class SlashCompleter(WordCompleter):
    def __init__(self):
        super().__init__(list(SLASH_COMMANDS.keys()), ignore_case=True, pattern=re.compile(r"[^\s]+"))

# Custom Style for prompt toolkit
prompt_style = Style.from_dict({
    'bottom-toolbar': '#FFFFFF bg:#0D2233',
    'prompt': '#29B5E8 bold',
})

def bottom_toolbar():
    prof = session.config.snowflake_profile or "default"
    mode = getattr(session, "current_mode", "plan")
    tasks = len(session.task_list)
    return HTML(f" ❄️ <b>SnowNinja</b> | Profile: {prof} | Mode: {mode} | Tasks: {tasks} | Type /help for commands ")

async def run_repl():
    print_welcome_splash()
    
    # Initialize components
    nim_client = NimClient()
    completer = SlashCompleter()
    pt_session = PromptSession(completer=completer, style=prompt_style)
    
    session.current_mode = "plan"
    
    while True:
        try:
            # Sync to Async bridge for prompt_toolkit
            user_input = await pt_session.prompt_async(
                "snowninja> ",
                bottom_toolbar=bottom_toolbar
            )
            user_input = user_input.strip()
            
            if not user_input:
                continue
                
            if user_input.startswith("/"):
                await handle_slash_command(user_input, nim_client)
            else:
                await handle_chat(user_input, nim_client)
                
        except KeyboardInterrupt:
            continue
        except EOFError:
            break
        except Exception as e:
            print_system_message(f"Fatal Error: {e}", is_error=True)

async def handle_slash_command(user_input: str, nim_client: NimClient):
    parts = user_input.split(" ", 1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    
    if cmd in ["/quit", "/exit"]:
        raise EOFError()
    elif cmd == "/help":
        help_text = "\n".join([f"**{k}**: {v}" for k, v in SLASH_COMMANDS.items()])
        print_agent_message(help_text, title="Available Commands")
    elif cmd == "/clear":
        console.clear()
        print_welcome_splash()
    elif cmd[1:] in MODES:
        session.current_mode = cmd[1:]
        print_system_message(f"Switched to {session.current_mode} mode.")
    elif cmd == "/interview":
        session.interview_mode = True
        session.interview_turn_count = 0
        print_system_message("Started requirements interview. Type /go to finish.")
        if args:
            await handle_chat(args, nim_client)
    elif cmd == "/go":
        session.interview_mode = False
        print_system_message("Interview ended. Proceeding to execution.")
    elif cmd == "/tasks":
        if not session.task_list:
            print_system_message("Task list is empty.")
        else:
            tasks_str = "\n".join([f"- [{t.status}] {t.title}: {t.description}" for t in session.task_list])
            print_agent_message(tasks_str, title="Current Tasks")
    elif cmd == "/skills":
        idx = SkillRouter.skill_index()
        print_agent_message(idx, title="Snowflake Skill Guides")
    elif cmd == "/profiles":
        profs = list_profiles()
        print_agent_message(", ".join(profs) if profs else "No profiles found in ~/.snowflake/connections.toml", title="Connection Profiles")
    elif cmd == "/profile":
        if args:
            session.config.snowflake_profile = args
            print_system_message(f"Profile set to {args}. Run /connection to test.")
        else:
            print_system_message("Usage: /profile <name>")
    elif cmd == "/connection":
        console.print("Testing connection...")
        res = test_connection(session.config.snowflake_profile)
        if res.get("status") == "success":
            print_system_message(f"Connected as {res.get('user')} on account {res.get('account')}")
        else:
            print_system_message(f"Connection failed: {res.get('error')}", is_error=True)
    elif cmd == "/model":
        if args.startswith("planner "):
            session.config.planner_model = args.split(" ")[1]
            print_system_message(f"Planner model set to {session.config.planner_model}")
        elif args.startswith("implementer "):
            session.config.implementer_model = args.split(" ")[1]
            print_system_message(f"Implementer model set to {session.config.implementer_model}")
        else:
            print_system_message("Usage: /model <planner|implementer> <model_name>")
    elif cmd == "/scaffold":
        from snowninja.scaffold.engine import create_dbt_project, create_streamlit_app, create_snowpark_project
        parts = args.split(" ")
        if len(parts) >= 2:
            scaffold_type = parts[0].lower()
            name = parts[1]
            try:
                if scaffold_type == "dbt":
                    path = create_dbt_project(name)
                elif scaffold_type == "streamlit":
                    path = create_streamlit_app(name)
                elif scaffold_type == "snowpark":
                    path = create_snowpark_project(name)
                else:
                    print_system_message(f"Unknown scaffold type: {scaffold_type}. Use dbt, streamlit, or snowpark.", is_error=True)
                    return
                print_system_message(f"Scaffolded {scaffold_type} project at {path}")
            except Exception as e:
                print_system_message(f"Scaffolding failed: {e}", is_error=True)
        else:
            print_system_message("Usage: /scaffold <dbt|streamlit|snowpark> <project_name>")
    else:
        print_system_message(f"Unknown command: {cmd}", is_error=True)

async def handle_chat(user_input: str, nim_client: NimClient):
    with console.status("[bold #29B5E8]Thinking...", spinner="dots"):
        if session.interview_mode:
            response = await nim_client.interview_chat(user_input)
            session.interview_turn_count += 1
            if "REQUIREMENTS_GATHERED" in response:
                session.interview_mode = False
                response = response.replace("REQUIREMENTS_GATHERED", "").strip()
                print_agent_message(response)
                print_system_message("Requirements finalized. Auto-switching to /plan mode.")
                session.current_mode = "plan"
            else:
                print_agent_message(response, title="Business Analyst")
        else:
            # Route skills
            skills = SkillRouter.route(user_input)
            context = ""
            for skill in skills:
                rules = SkillRouter.load_critical_rules(skill)
                if rules:
                    context += f"\n\nRules for {skill}:\n{rules}"
            
            prompt = user_input
            if context:
                prompt += f"\n\nCRITICAL CONTEXT:\n{context}"
                
            role = MODES.get(session.current_mode, ModelRole.PLANNER)
            response = await nim_client.agent_chat(prompt, role=role)
            print_agent_message(response)
