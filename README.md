# ❄️ SnowNinja CLI

**The Principal Architect’s Workbench for the Snowflake Ecosystem.**

[![NIM Powered](https://img.shields.io/badge/LLM-NVIDIA_NIM-76B900?style=for-the-badge&logo=nvidia)](https://www.nvidia.com/en-us/ai-data-science/generative-ai/nim/)
[![Snowflake](https://img.shields.io/badge/Cloud-Snowflake-29B5E8?style=for-the-badge&logo=snowflake)](https://www.snowflake.com/)

SnowNinja is a high-performance, agentic TUI (Terminal User Interface) designed for Snowflake engineers and architects. It provides a production-grade autonomous agent harness backed by **NVIDIA NIM** models, enabling full-cycle data engineering—from requirement gathering to live pipeline implementation—directly from your terminal.

---

## 🥷 The Agentic Philosophy

SnowNinja operates on a **Dual-Lane Execution Model**, separating reasoning from implementation to ensure maximum architectural integrity:

1.  **📐 The Planner Lane:** Backed by `meta/llama-3.1-405b-instruct` (via NIM). The Planner focuses on high-level reasoning, Snowflake architecture, and environment exploration. It produces structured **Task Lists**.
2.  **⚙️ The Implementer Lane:** Backed by `qwen/qwen2.5-coder-32b-instruct` (via NIM). The Implementer consumes the Planner's task list and executes live Snowflake operations (DDL, DML, Python, Shell) to build the solution.

---

## 🚀 Quick Start

```bash
# 1. Clone and Initialize
git clone https://github.com/Jericho2010/TUI-snowNinja-cli.git
cd TUI-snowNinja-cli
./setup.sh

# 2. Configure Credentials
snowninja setup

# 3. Verify Connection
snowninja doctor

# 4. Launch the Cockpit
snowninja
```

---

## 💎 Feature Matrix

| Feature | Description | Status |
| :--- | :--- | :--- |
| **Dual-Lane Loop** | Separate Planner/Implementer lanes for architectural rigor. | ✅ Production |
| **Resilient NIM Client** | Auto-fallback chain (Llama → Mistral → Qwen) for 100% uptime. | ✅ Production |
| **Snowflake Action Tools** | 45+ built-in tools for UC, Cortex, Warehouses, and Pipelines. | ✅ Production |
| **Interactive Interview** | `/interview` mode for guided requirements gathering. | ✅ Production |
| **Dynamic Skill Router** | RAG-style injection of domain-specific Snowflake guides. | ✅ Production |
| **Project Scaffolding** | `/scaffold` for instantly creating Medallion/Snowpark repos. | ✅ Production |
| **Safe Shell Execution** | Gated subprocess execution for local ops (git, uv, snow). | ✅ Production |

---

## 📂 Documentation

*   [**Architecture Reference**](docs/ARCHITECTURE.md): Deep-dive into the async loops, fallback chains, and tool integration.
*   [**Command Manual**](docs/COMMANDS.md): Comprehensive guide to slash commands and TUI navigation.
*   [**Launch Strategy**](docs/LAUNCH_POST.md): Announcement template for high-engagement release.

---

## 🛡️ Security & Privacy

SnowNinja is designed with a **"Private by Design"** architecture:
- **No Hardcoded Secrets**: Your Snowflake credentials and NVIDIA API keys are never stored in this repository.
- **Local Persistence**: All sensitive data is stored in `~/.snowninja/config.yaml` on your local machine.
- **Safe Execution**: Local shell commands are gated by a strict allowlist.

For more details, see [SECURITY.md](SECURITY.md).

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on reporting bugs or submitting pull requests.

---

## 📜 License

Built with ❄️ and 🥷 by the SnowNinja Team. Part of the AI-Dev-Kit ecosystem. Licensed under the [MIT License](LICENSE).
