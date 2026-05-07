import json
import logging
import asyncio
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
import traceback

from snowninja.session import session
from snowninja.actions.tools_core import SNOWFLAKE_TOOLS, TOOL_DISPATCH
from snowninja.llm.models import ModelRole, PLANNER_FALLBACK_CHAIN, IMPLEMENTER_FALLBACK_CHAIN, NO_TOOLS_MODELS

logger = logging.getLogger(__name__)

SYSTEM_PROMPTS = {
    ModelRole.PLANNER: """You are the SnowNinja Planner, a Principal Snowflake Architect.
Your job is to analyze the user's intent, query Snowflake metadata if necessary to understand the environment, and produce a detailed plan.
Do NOT execute DDL or DML. Only read metadata.
When you are done planning, output a section starting with '## Task List' outlining the steps for the Implementer.""",

    ModelRole.IMPLEMENTER: """You are the SnowNinja Implementer, an expert Snowflake Data Engineer.
Your job is to execute the tasks outlined in the plan.
You can execute SQL, create objects, and manage the Snowflake environment using your tools.
Always validate SQL before executing it if it is complex."""
}

INTERVIEW_SYSTEM_PROMPT = """You are a Snowflake Business Analyst helping scope a new data requirement.
Ask clarifying questions one at a time. Be concise. Use Snowflake terminology where appropriate.
When you have enough information, end your response with 'REQUIREMENTS_GATHERED'."""

class NimClient:
    def __init__(self):
        # The openai client requires an API key. We will pass it per request or init it here.
        self._get_client()

    def _get_client(self):
        pat = session.config.nvidia_pat
        if not pat:
            # We'll handle this gracefully in the CLI, but we need a dummy key for initialization
            pat = "dummy_key_to_prevent_crash_if_unconfigured"
        return AsyncOpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=pat
        )

    def _get_model_for_role(self, role: ModelRole) -> str:
        if role == ModelRole.PLANNER:
            return session.config.planner_model
        return session.config.implementer_model

    def _get_fallback_chain(self, role: ModelRole) -> List[str]:
        if role == ModelRole.PLANNER:
            return PLANNER_FALLBACK_CHAIN
        return IMPLEMENTER_FALLBACK_CHAIN

    async def _execute_tool(self, name: str, args: Dict[str, Any]) -> str:
        if name not in TOOL_DISPATCH:
            return json.dumps({"status": "error", "message": f"Tool '{name}' not found."})
        
        func = TOOL_DISPATCH[name]
        try:
            # Check if function is async (we made them sync in tools_core, but good practice)
            if asyncio.iscoroutinefunction(func):
                result = await func(**args)
            else:
                # Run sync functions in thread pool to avoid blocking
                result = await asyncio.to_thread(func, **args)
            
            if isinstance(result, str):
                return result
            return json.dumps(result, default=str)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e), "traceback": traceback.format_exc()})

    async def agent_chat(self, prompt: str, role: ModelRole = ModelRole.PLANNER) -> str:
        client = self._get_client()
        primary_model = self._get_model_for_role(role)
        chain = [primary_model] + [m for m in self._get_fallback_chain(role) if m != primary_model]
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPTS[role]},
            {"role": "user", "content": prompt}
        ]

        # Max 20 tool-calling iterations to prevent infinite loops
        for iteration in range(20):
            response_msg = None
            
            # Try fallback chain
            for model in chain:
                try:
                    kwargs = {
                        "model": model,
                        "messages": messages,
                        "temperature": 0.2
                    }
                    if model not in NO_TOOLS_MODELS:
                        kwargs["tools"] = SNOWFLAKE_TOOLS
                        kwargs["tool_choice"] = "auto"
                        kwargs["parallel_tool_calls"] = False

                    response = await client.chat.completions.create(**kwargs)
                    response_msg = response.choices[0].message
                    break # Success, break fallback loop
                except Exception as e:
                    logger.warning(f"Model {model} failed: {e}")
                    continue
            
            if not response_msg:
                return "Error: All models in the fallback chain failed."

            messages.append(response_msg)

            # Check if there are tool calls
            if hasattr(response_msg, "tool_calls") and response_msg.tool_calls:
                for tool_call in response_msg.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        tool_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        tool_args = {}
                    
                    tool_result = await self._execute_tool(tool_name, tool_args)
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": tool_name,
                        "content": tool_result
                    })
            else:
                # No more tool calls, return final response
                return response_msg.content or ""
                
        return "Error: Exceeded maximum tool iterations (20)."

    async def interview_chat(self, user_input: str) -> str:
        client = self._get_client()
        model = self._get_model_for_role(ModelRole.PLANNER)
        
        # In a real app we'd keep conversation history in the session.
        # For simplicity here, we simulate it.
        messages = [
            {"role": "system", "content": INTERVIEW_SYSTEM_PROMPT},
            {"role": "user", "content": f"I want to build this: {user_input}"}
        ]
        
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"Error during interview: {e}"
