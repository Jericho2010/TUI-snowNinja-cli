# SnowNinja — Command Manual

SnowNinja is controlled via interactive slash commands. This guide details every command, its parameters, and the underlying logic it triggers in the agentic harness.

---

## 📐 Planning & Design

### `/plan <goal>`
Switch to **Planner Mode**. This sets the model role to `planner`, which uses high-reasoning models (Llama 4 Maverick) to architect a solution.
- **Under the Hood**: Injects a strict system prompt that forbids code generation and mandates a `## Task List` at the end of the response.
- **Example**: `/plan Design a medallion pipeline for clickstream data in the analytics_db catalog.`

### `/interview <goal>`
Activate the **Requirements Analyst**. This starts a guided Q&A session to gather project specifications before a single line of code is written.
- **Under the Hood**: Uses a separate LLM conversation history to avoid polluting the main agent context. Closes after 5 questions or upon `/go`.
- **Output**: Generates a combined `## Requirements` and `## Task List` section.

### `/go`
Force the current interview to finalize.
- **Under the Hood**: Triggers the `force_finalize=True` flag in the `interview_chat` loop, prompting the model to summarize everything gathered so far into a project plan.

---

## ⚙️ Implementation & Execution

### `/implement [instruction]`
Switch to **Implementer Mode**. This uses coding-optimized models (Qwen 3 Coder 480B) to execute the active task list.
- **Under the Hood**: Injects the `session.task_list` and `session.requirements` directly into the system prompt. The model will automatically pick up where it left off.
- **Example**: `/implement start` or `/implement build the staging tables`.

### `/explore`
A semantic alias for the Implementer lane, optimized for read-only workspace inspection.
- **Under the Hood**: Sets the mode to `explore` and model role to `implementer`. This allows the model to run `execute_sql` for data analysis without feeling forced to generate an architectural plan.

### `/operate`
Switch to **Operate Mode** for hands-on execution against Snowflake resources.
- **Best for**: Running SQL, working through pipeline tasks, and carrying out live implementation work with an operational mindset.

### `/govern`
Switch to **Govern Mode** for security- and policy-oriented reasoning.
- **Best for**: Roles, grants, access reviews, governance guardrails, and policy-aware planning.

### `/cost`
Switch to **Cost Mode** for warehouse and spend-aware reasoning.
- **Best for**: Warehouse sizing, credit efficiency, and performance/cost trade-offs.

---

## 🎛 System & Configuration

### `/models`
Display the **NIM Model Registry**.
- **Planner Lane**: Shows the primary and fallback reasoning models.
- **Implementer Lane**: Shows the primary and fallback coding models.

### `/model <lane> <model_id>`
Hot-swap a model for the current session.
- **Example**: `/model planner meta/llama-4-maverick-17b-128e-instruct`
- **Persistence**: Saves the preference to `~/.snowninja/config.yaml` and resets the `NimClient`.

### `/tasks`
Display the current session's active plan.
- **Subcommand**: `/tasks clear` — Wipes the task list and requirements from the session.

### `/connection`
Show the current Snowflake connection status.
- **Output**: Active profile plus a live authentication check, including current user, role, and warehouse when available.

### `/tools`
List all loaded Snowflake action tools.
- **Use this when**: You want to see the callable tool surface available to the harness at runtime.

### `/skills [name]`
List the loaded skill guides, or show the full content of one skill.
- **Example**: `/skills snowflake-streamlit`

### `/history`
Show the current session's conversation history.
- **Use this when**: You want to inspect what the active lane has already seen during the current shell session.

---

## 🏗 Project Scaffolding

### `/scaffold <template>`
Generate local project files from pre-defined Snowflake templates.
- **Templates**:
    - `pipeline-project`: Dynamic Tables medallion pipeline starter.
    - `app-project`: Streamlit in Snowflake application starter.
    - `cortex-project`: Cortex AI document/LLM pipeline starter.
    - `snowpark-project`: Snowpark Python UDF / stored procedure starter.
- **Tip**: Run `/scaffold` with no argument to see the interactive scaffold menu.

---

## 🥷 Utility Commands

- `/help`: Show all available commands.
- `/new`: Hard reset. Clears history, tasks, requirements, and interview state.
- `/clear`: Clear conversation history only (keeps the task list).
- `/quit`: Exit the shell.
- `/exit`: Exit the shell.

---

## 🧪 Non-Interactive CLI Commands

These commands are run from your terminal, not inside the interactive shell:

- `snowninja setup`: Configure Snowflake and NVIDIA credentials.
- `snowninja doctor`: Run environment and connectivity diagnostics.
- `snowninja`: Launch the interactive TUI shell.

---

*Part of [SnowNinja](../README.md) — The Principal Architect’s Shell.* 🥷❄️
