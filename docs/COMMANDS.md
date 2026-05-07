# SnowNinja Command Reference

SnowNinja is controlled via a series of interactive slash commands. This guide explains how to use each command to drive the agentic loop.

---

## 🛠 Core Workflow Commands

### `/plan <goal>`
Switch to **Planner Mode**. Use this for high-level architectural design or when you need the agent to reason about your Snowflake environment.
- **Output**: Generates a technical plan and a `## Task List`.

### `/implement [instruction]`
Switch to **Implementer Mode**. This lane picks up the active Task List and begins autonomous execution.
- **Example**: `/implement start` or `/implement build the staging tables`.

### `/interview <goal>`
Start a guided requirements gathering session. The agent will ask you 5 focused questions to shape the project requirements before generating a plan.
- **Exit**: Type `/go` at any time to skip the remaining questions and finalize the requirements.

---

## 🔍 Inspection & Governance

### `/explore`
Switch to a read-only exploration mode. The Implementer model will focus on running `SELECT` queries and describing objects to help you understand your data.

### `/govern`
Switch to the Governance lane. Optimized for managing Roles, Grants, and masking policies.

### `/connection`
Run an immediate diagnostic on your Snowflake connection. Shows your current user, role, warehouse, and database context.

---

## 🎛 System Management

### `/models`
Display the NIM Model Registry. Shows all available Planner and Implementer models and their current fallback status.

### `/model <lane> <id>`
Hot-swap a model for the current session.
- **Example**: `/model planner meta/llama-3.1-70b-instruct`

### `/tasks`
Display the current active Task List and gathered requirements.
- **Wipe**: `/tasks clear` to reset the project state.

### `/new`
A full "hard reset". Clears conversation histories, the task list, requirements, and any active interview state.

---

## 🏗 Project Scaffolding

### `/scaffold <template>`
Instantly generate a project structure on your local machine.
- **Available Templates**:
    - `pipeline-project`: A dbt/SQL-based Medallion architecture structure.
    - `app-project`: A Streamlit in Snowflake (SiS) template.
    - `snowpark-project`: A Python-native Snowpark development environment.
