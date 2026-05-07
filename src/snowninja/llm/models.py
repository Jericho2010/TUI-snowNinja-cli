from enum import Enum

class NimModel(str, Enum):
    # Reasoning / Planner Models (Maverick / Next-Gen)
    LLAMA_4_MAVERICK = "meta/llama-4-maverick-17b-128e-instruct"
    MISTRAL_LARGE_3 = "mistralai/mistral-large-3-675b-instruct-2512"
    
    # Coding / Implementer Models (Next-Gen)
    QWEN_3_CODER = "qwen/qwen3-coder-480b-a35b-instruct"
    DEEPSEEK_V4_PRO = "deepseek-ai/deepseek-v4-pro"
    DEEPSEEK_V4_FLASH = "deepseek-ai/deepseek-v4-flash"
    GLM_5_1 = "z-ai/glm-5.1"

class ModelRole(str, Enum):
    PLANNER = "planner"
    IMPLEMENTER = "implementer"
