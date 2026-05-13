# SnowNinja — Architecture Reference

> **Living document.** Updated as the system evolves.
> Last updated: 2026-05-14 · [← Back to README](../README.md)

---

## Contents

1. [System Overview](#1-system-overview)
2. [Dual-Lane AI Design](#2-dual-lane-ai-design)
3. [Request Lifecycle](#3-request-lifecycle)
4. [Codebase Component Map](#4-codebase-component-map)
5. [Planner → Implementer: End-to-End Example](#5-planner--implementer-end-to-end-example)
6. [Skills Guidance Layer](#6-skills-guidance-layer)
7. [Guided Requirements Interview](#7-guided-requirements-interview)
8. [Snowflake Action Tools](#8-snowflake-action-tools)
9. [Project Structure](#9-project-structure)

---

## 1. System Overview

```mermaid
flowchart LR
    classDef user fill:#1a1a2e,stroke:#29B5E8,color:#fff,font-weight:bold
    classDef shell fill:#1B3B52,stroke:#29B5E8,color:#fff
    classDef nim fill:#0d2233,stroke:#76B900,color:#fff
    classDef snow fill:#29B5E8,stroke:#1A82A8,color:#fff
    classDef store fill:#37474f,stroke:#90a4ae,color:#ccc,stroke-dasharray:4

    U(["👤 You\n(Terminal)"]):::user
    SN["🥷 SnowNinja Shell\nprompt_toolkit REPL"]:::shell
    NIM["⚡ NVIDIA NIM\nOpenAI-compatible API"]:::nim
    SNOW[("❄️ Snowflake\nData Cloud")]:::snow
    CFG[("⚙️ ~/.snowninja/\nconfig.yaml")]:::store
    LOCAL[("📁 Local Filesystem\n& Shell")]:::store

    U -->|"natural language"| SN
    SN -->|"structured LLM call"| NIM
    NIM -->|"tool_call events"| SN
    SN -->|"Snowflake Python Connector"| SNOW
    SNOW -->|"live data"| SN
    SN -->|"rendered response"| U
    SN -->|"write_local_file\nrun_shell_command"| LOCAL
    CFG -.->|"PATs & profile config"| SN
```

SnowNinja acts as an **intelligent broker** between the Snowflake Data Cloud, NVIDIA NIM’s generative power, and your local filesystem. It translates natural language intent into a structured tool-calling loop. When the LLM requires environmental context (e.g., "what tables are in the SALES schema?"), the shell executes a real Snowflake query and feeds the result back to the model, ensuring every plan is grounded in reality.

---

## 2. Dual-Lane AI Design

```mermaid
flowchart TD
    classDef lane fill:#0d2233,stroke:#29B5E8,color:#fff,font-weight:bold
    classDef model fill:#1B3B52,stroke:#56C9F2,color:#fff
    classDef shared fill:#1A82A8,stroke:#29B5E8,color:#fff
    classDef tool fill:#29B5E8,stroke:#1A82A8,color:#fff
    classDef snow fill:#F4F7F9,stroke:#29B5E8,color:#1B3B52,stroke-dasharray:3
    classDef local fill:#37474f,stroke:#90a4ae,color:#ccc

    subgraph PLANNER ["📐 Planner Lane  /plan"]
        PM["llama-4-maverick\n★ DEFAULT · reasoning"]:::model
        PF["mistral-large-3\nFALLBACK · reliable"]:::model
        PM -.->|"auto-fallback if overloaded"| PF
    end

    subgraph IMPL ["⚙️ Implementer Lane  /implement"]
        IM["qwen3-coder-480b\n★ DEFAULT · best coder"]:::model
        IM2["deepseek-v4-flash / mistral-small-4 / deepseek-v4-pro\nalternatives"]:::model
    end

    subgraph SHARED ["🔗 Shared Session State"]
        TL["📋 session.task_list\n(markdown checklist)"]:::shared
        REQ["📝 session.requirements\n(from /interview)"]:::shared
    end

    subgraph TOOLS ["🔧 Action Tools (40+ built-in)"]
        T1["Database Ops\ndbs · schemas · tables"]:::tool
        T2["Compute & SQL\nwarehouses · execute_sql"]:::tool
        T3["Cortex ML\ncomplete · summarize · sentiment"]:::tool
        T4["Pipelines\nDynamic Tables · Tasks"]:::tool
        T5["Governance\nroles · grants · policies"]:::tool
        T6["Local Ops\nwrite_file · run_shell"]:::local
    end

    SNOW[("❄️ Snowflake\nData Cloud")]:::snow

    PLANNER -->|"## Task List saved"| TL
    REQ -->|"injected into system prompt"| IMPL
    TL -->|"injected into system prompt"| IMPL
    IMPL --> TOOLS
    PLANNER --> TOOLS
    TOOLS <--> SNOW
```

SnowNinja separates **Architectural Reasoning** from **Technical Execution**:
- **Planner lane**: Uses the highest-reasoning models (`llama-4-maverick`) to decompose complex goals into a structured `## Task List`.
- **Implementer lane**: Uses coding-specialized models (`qwen3-coder-480b`) to execute those tasks.
- **Shared Context**: The `session.task_list` is the source of truth that connects the two models.

---

## 3. Request Lifecycle

```mermaid
sequenceDiagram
    participant U as 👤 You
    participant R as 🥷 REPL Shell
    participant S as ❄️ Spinner / Live UI
    participant SK as 📚 Skill Router
    participant N as 🤖 NIM API
    participant T as 🔧 Tool Executor
    participant D as ❄️ Snowflake

    U->>R: Type message + Enter
    R->>SK: route(message) → skill match
    SK-->>R: inject skill context ephemerally
    R->>S: Show "📚 Skills: cortex-ml | Calling llama-4-maverick…"
    R->>N: chat.completions.create(model, messages+skill_ctx, tools)

    alt Model calls a tool
        N-->>R: tool_call event (fn_name, fn_args)
        R->>S: Show "🔧 execute_sql(...)…"
        R->>T: execute_tool(fn_name, fn_args)
        T->>D: Snowflake SQL Execution
        D-->>T: Result set
        T-->>R: JSON result
        R->>S: Show "✓ execute_sql → 5 items"
        R->>N: Append tool result, continue loop
    end

    alt Model is overloaded
        N-->>R: 429 / 503 error
        R->>S: Show "⚡ Fallback → mistral-large"
        R->>N: Retry with fallback model
    end

    N-->>R: Final text response
    R->>S: Stop spinner
    R->>U: Render Markdown response

    opt Planner mode & ## Task List detected
        R->>R: Extract task list → session.task_list
        R->>U: Show "📋 Task list saved" banner
    end
```

The lifecycle is built on **Async Generators**. The TUI does not block; it streams events (text chunks, tool calls, model switches) directly into the `Rich.Live` buffer.

---

## 4. Codebase Component Map

```mermaid
flowchart TD
    classDef entry fill:#29B5E8,stroke:#1A82A8,color:#fff,font-weight:bold
    classDef core fill:#1B3B52,stroke:#29B5E8,color:#fff
    classDef llm fill:#0d2233,stroke:#76B900,color:#fff
    classDef actions fill:#29B5E8,stroke:#56C9F2,color:#fff
    classDef skills fill:#1A82A8,stroke:#29B5E8,color:#fff
    classDef repl fill:#1a1a2e,stroke:#29B5E8,color:#fff
    classDef test fill:#37474f,stroke:#90a4ae,color:#ccc

    CLI["cli.py\n🚀 Entry Point\nTyper commands"]:::entry

    subgraph CORE ["Core"]
        CFG["core/config.py\nCredential load/save\nSnowNinjaConfig"]:::core
        SES["session.py\nGlobal state\ntask_list · requirements"]:::core
    end

    subgraph LLM ["LLM Layer"]
        NIM["llm/nim_client.py\nNimClient\nagent_chat + interview_chat loops\nfallback chain · skill injection"]:::llm
    end

    subgraph ACTIONS ["Action Layer"]
        TC["actions/tools_core.py\nSnowflake SDK tools\nlist · create · execute"]:::actions
    end

    subgraph SKILLS ["Skills Layer"]
        RT["skills/router.py\nSkillRouter\nkeyword scoring"]:::skills
        SK["skills/*.md\nSnowflake Skill Guides"]:::skills
    end

    subgraph REPL ["REPL Shell"]
        SH["repl/shell.py\nSnowNinjaShell\nprompt_toolkit · Rich · Live"]:::repl
    end

    subgraph TESTS ["Tests"]
        UT["tests/unit/\nconfig · tools · dispatch"]:::test
        E2E["tests/e2e/\nCLI · doctor · agent"]:::test
    end

    CLI --> SH
    CLI --> CFG
    SH --> NIM
    SH --> SES
    NIM --> TC
    NIM --> RT
    RT --> SK
    NIM --> SES
    CFG --> SES
```

---

## 5. Guided Requirements Interview

The `/interview <goal>` command activates a dedicated **Requirements Analyst** persona.

```mermaid
flowchart TD
    A["User: /interview <goal>"] --> B["SkillRouter.route(goal)\ninject domain context into analyst"]
    B --> C["INTERVIEW_SYSTEM_PROMPT\n+ skill context → interview_chat()"]
    C --> D["Analyst asks ONE focused\nmultiple-choice question"]
    D --> E["User answers"]
    E --> F{Turn < 5 and\nanalyst not ready?}
    F -->|yes| D
    F -->|no| G["/go triggered\n(auto or manual)"]
    G --> H["Analyst generates\n## Requirements + ## Task List"]
    H --> I["session.requirements saved\nsession.task_list saved"]
    I --> J["Both injected into\nImplementer context on /implement"]
```

The interview lane is isolated from the main agent history, preventing "context pollution" during long-running sessions.

---

## 6. Snowflake Action Tools

Full registry in `src/snowninja/actions/tools_core.py`.

| Category | Tools |
| :--- | :--- |
| **Metadata** | `list_databases`, `list_schemas`, `list_tables`, `describe_table`, `search_objects` |
| **Compute** | `list_warehouses`, `execute_sql` |
| **Cortex AI** | `cortex_complete`, `cortex_summarize`, `cortex_sentiment`, `cortex_extract` |
| **Pipelines** | `list_dynamic_tables`, `list_tasks`, `create_task` |
| **Governance** | `get_current_user`, `list_roles`, `list_grants` |
| **Local Ops** | `write_local_file`, `run_shell_command` |

---

## 7. Project Structure

- `src/snowninja/cli.py`: Typer entry point.
- `src/snowninja/llm/nim_client.py`: The agent loop and fallback mechanics.
- `src/snowninja/repl/shell.py`: The prompt-toolkit UI and slash commands.
- `src/snowninja/skills/`: Markdown skill guides for RAG-style injection.
- `tests/`: Comprehensive unit and E2E test suite.

---

*Part of [SnowNinja](../README.md) — The Principal Architect’s Shell.* 🥷❄️
