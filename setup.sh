#!/usr/bin/env bash
set -e

echo "=== SnowNinja CLI Setup ==="

# ── Check Python version ──────────────────────────────────────────────────────
PYTHON_VERSION=$(python3 -c 'import sys; print(sys.version_info >= (3, 10))' 2>/dev/null || echo "False")
if [[ "$PYTHON_VERSION" != "True" ]]; then
    echo "ERROR: Python 3.10+ is required."
    echo "  Install it from https://www.python.org/downloads/ or via your system package manager."
    exit 1
fi
echo "  ✓ Python $(python3 --version)"

# ── Ensure uv is available ────────────────────────────────────────────────────
if ! command -v uv &> /dev/null; then
    echo "  uv not found — installing via official installer..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Add uv to PATH for this session
    export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
fi

if ! command -v uv &> /dev/null; then
    echo "ERROR: uv installation failed."
    echo "  Install manually: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi
echo "  ✓ uv $(uv --version)"

# ── Create virtualenv and install ────────────────────────────────────────────
echo "  Creating virtual environment..."
uv venv .venv
source .venv/bin/activate

echo "  Installing snowninja and dependencies..."
uv pip install -e .[dev]

echo ""
echo "=== Setup Complete ==="
echo "  Run 'snowninja setup' to configure your credentials, then:"
echo "  Run 'snowninja' to launch the agent shell."
echo ""
echo "  Or use './run.sh' to launch directly from this directory."
