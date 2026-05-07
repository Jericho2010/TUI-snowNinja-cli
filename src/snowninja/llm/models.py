from enum import Enum

class ModelRole(str, Enum):
    PLANNER = "planner"
    IMPLEMENTER = "implementer"
    CORTEX = "cortex"

# Fallback chains for when the primary model fails
PLANNER_FALLBACK_CHAIN = [
    "meta/llama-3.3-70b-instruct",
    "meta/llama-3.1-70b-instruct",
    "meta/llama-3.1-8b-instruct"
]

IMPLEMENTER_FALLBACK_CHAIN = [
    "meta/llama-3.3-70b-instruct",
    "meta/llama-3.1-70b-instruct",
    "meta/llama-3.1-8b-instruct"
]

# Models that do not support tool calling (used for text-only flows)
NO_TOOLS_MODELS = [
    "google/gemma-7b-it",
    "google/gemma-2b-it"
]
