from enum import Enum

class NimModel(str, Enum):
    # Reasoning / Planner Models
    LLAMA_3_1_405B = "meta/llama-3.1-405b-instruct"
    MISTRAL_LARGE = "mistralai/mistral-large-2411"
    
    # Coding / Implementer Models
    QWEN_2_5_CODER_32B = "qwen/qwen2.5-coder-32b-instruct"
    DEEPSEEK_CODER_V2 = "deepseek-ai/deepseek-coder-v2-instruct"

class ModelRole(str, Enum):
    PLANNER = "planner"
    IMPLEMENTER = "implementer"
