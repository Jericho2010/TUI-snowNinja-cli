#!/usr/bin/env bash
set -e

# Automatically activate the virtual environment if not already activated
if [[ -z "${VIRTUAL_ENV}" ]]; then
    if [[ -d ".venv" ]]; then
        source .venv/bin/activate
    else
        echo "Virtual environment not found. Please run ./setup.sh first."
        exit 1
    fi
fi

# Pass any given arguments directly to the snowninja CLI
snowninja "$@"
