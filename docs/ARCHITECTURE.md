# SnowNinja Architecture

SnowNinja is a **Compound AI System** designed to operate as a high-fidelity agent harness for the Snowflake Data Cloud. This document details the technical implementation of its agentic loops, state management, and tool integration.

---

## 1. Dual-Lane Agent Logic

SnowNinja bifurcates the agentic workflow into two specialized lanes to reduce hallucination and ensure architectural rigor.

### A. The Planner Lane (Reasoning)
- **Primary Model**: `meta/llama-3.1-405b-instruct`
- **Objective**: Environmental exploration and plan generation.
- **Workflow**: 
    1. Receives a high-level goal from the user.
    2. Uses exploration tools (`list_databases`, `search_objects`, `describe_table`) to inspect the live Snowflake environment.
    3. Analyzes requirements (optionally gathered via `/interview`).
    4. Outputs a structured `## Task List` which is parsed and saved to the session state.

### B. The Implementer Lane (Execution)
- **Primary Model**: `qwen/qwen2.5-coder-32b-instruct`
- **Objective**: Code generation and autonomous tool execution.
- **Workflow**:
    1. Receives the `## Task List` from the Planner lane injected into its system prompt.
    2. Works through tasks sequentially.
    3. Uses execution tools (`execute_sql`, `write_local_file`, `run_shell_command`) to build the solution.

---

## 2. The Resilient NIM Client

The `NimClient` (`src/snowninja/llm/nim_client.py`) is the heart of the engine. It features a sophisticated fallback mechanism to ensure the agent stays operational even during NIM API instability.

### Proactive Model Resolution
Before every chat completion, the client pings the primary model. If it detects a 429 (Rate Limit), 503 (Overloaded), or 404 (Not Found), it automatically walks down the **Fallback Chain**:
- **Planner Chain**: `llama-3.1-405b` → `mistral-large-3` → `qwen-2.5-coder-32b`.
- **Implementer Chain**: `qwen-2.5-coder-32b` → `deepseek-v3` → `mistral-large-3`.

---

## 3. Tool Dispatch & Security

SnowNinja utilizes the `ToolsCore` framework to interface with the **Snowflake Python Connector**.

### Execution Safety
The agent can execute arbitrary SQL on your warehouse via `execute_sql`. To prevent catastrophic errors during autonomous loops:
- The agent is restricted to the permissions of the role configured in your Snowflake profile.
- Shell execution is restricted to a pre-defined allowlist of safe commands (git, uv, snow, etc.).

---

## 4. TUI State Management

The interactive shell (`src/snowninja/repl/shell.py`) manages a persistent `Session` object:
- **Conversation Persistence**: Separate histories are maintained for `/plan` and `/implement`.
- **Task List Persistence**: The extraction of `## Task List` from the Planner's output ensures the Implementer always knows its current objective, even across session restarts.
- **Interview Mode**: A specialized modal state that switches the agent to a requirements-gathering persona before transitioning back to the main loop.
