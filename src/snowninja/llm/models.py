from enum import Enum

class NimModel(str, Enum):
    DEEPSEEK_V4 = "deepseek-ai/deepseek-v4-pro"
    KIMI_LATEST = "moonshotai/kimi-k2.6"
    QWEN_CODER_LATEST = "qwen/qwen3-coder-480b-a35b-instruct"
    GLM_LATEST = "z-ai/glm-5.1"
    MISTRAL_LATEST = "mistralai/mistral-large-3-675b-instruct-2512"

class ModelRole(str, Enum):
    PLANNER = "planner"
    IMPLEMENTER = "implementer"
