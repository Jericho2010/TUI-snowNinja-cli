from enum import Enum

class NimModel(str, Enum):
    # Planning / Reasoning Models (The Thinkers)
    LLAMA_4_MAVERICK = "meta/llama-4-maverick-17b-128e-instruct"
    MISTRAL_LARGE_3 = "mistralai/mistral-large-3-675b-instruct-2512"
    NEMOTRON_4_340B = "nvidia/nemotron-4-340b-instruct"
    GEMMA_4_31B = "google/gemma-4-31b-it"

    # Coding / Implementer Models (The Builders)
    QWEN_3_CODER = "qwen/qwen3-coder-480b-a35b-instruct"
    DEEPSEEK_V4_FLASH = "deepseek-ai/deepseek-v4-flash"
    MISTRAL_SMALL_4 = "mistralai/mistral-small-4-119b-2603"
    DEEPSEEK_V4_PRO = "deepseek-ai/deepseek-v4-pro"

    # Specialized Tiers (v3+ only)
    KIMI_2_6 = "moonshotai/kimi-k2.6"
    KIMI_THINKING = "moonshotai/kimi-k2-thinking"

class ModelRole(str, Enum):
    PLANNER = "planner"
    IMPLEMENTER = "implementer"
