# ❄️ SnowNinja CLI

**The Principal Architect’s Workbench for the Snowflake Ecosystem.**

SnowNinja is a high-performance, agentic TUI (Terminal User Interface) designed for Snowflake engineers and architects. It provides a production-grade autonomous agent harness backed by **NVIDIA NIM** models, enabling full-cycle data engineering—from requirement gathering to live pipeline implementation—directly from your terminal.

---

## 🥷 The Agentic Philosophy

SnowNinja operates on a **Dual-Lane Execution Model**, separating reasoning from implementation to ensure maximum architectural integrity:

1.  **📐 The Planner Lane:** Backed by `meta/llama-3.1-405b-instruct` (via NIM). The Planner focuses on high-level reasoning, Snowflake architecture, and environment exploration. It produces structured **Task Lists**.
2.  **⚙️ The Implementer Lane:** Backed by `qwen/qwen2.5-coder-32b-instruct` (via NIM). The Implementer consumes the Planner's task list and executes live Snowflake operations (DDL, DML, Python, Shell) to build the solution.

---

## 🚀 Quick Start

### 1. Installation
Clone the repository and install in editable mode using `uv`:

```bash
git clone https://github.com/Jericho2010/TUI-snowNinja-cli.git
cd TUI-snowNinja-cli
./setup.sh
```

### 2. Configuration
Run the setup wizard to configure your NVIDIA PAT and Snowflake connection:

```bash
snowninja setup
```

### 3. Verify
Run the diagnostics tool to ensure all systems are go:

```bash
snowninja doctor
```

### 4. Launch
Start the interactive cockpit:

```bash
snowninja
```

---

## 🛠 Features

- **Autonomous Agentic Loop**: Built-in tool calling for the Snowflake Python SDK, SQL execution, and local file I/O.
- **Resilient Fallbacks**: Multi-stage model fallback logic to handle NVIDIA NIM API rate limits or capacity issues automatically.
- **Interactive Interview Flow**: Use `/interview` to let the agent guide you through requirements gathering before building a plan.
- **Project Scaffolding**: Use `/scaffold` to instantly generate local templates for Medallion Pipelines, Streamlit apps, or Snowpark projects.
- **Dynamic Skill Injection**: RAG-style skill routing that injects domain-specific Snowflake guides into the agent's context on the fly.

---

## 📂 Documentation

- [**Architecture Guide**](docs/ARCHITECTURE.md): Deep dive into the dual-lane agent harness.
- [**Command Reference**](docs/COMMANDS.md): Full manual for slash commands and TUI navigation.
- [**Launch Post**](docs/LAUNCH_POST.md): Announcement template for social sharing.

---

## 📜 License

Built with ❄️ and 🥷 by the SnowNinja Team.
