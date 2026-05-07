import json
import logging
import asyncio
import traceback
from typing import AsyncGenerator, Dict, Any, List, Optional, Tuple

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from snowninja.session import session
from snowninja.llm.models import NimModel, ModelRole
from snowninja.actions.tools_core import tools
from snowninja.skills.router import skill_router

logger = logging.getLogger(__name__)

# Models that don't support tool calling endpoints, meaning we need to use a standard chat format.
NO_TOOLS_MODELS = [
    "nvidia/llama-3.1-nemotron-ultra-253b-v1",
    "qwen/qwen2.5-coder-32b-instruct"
]

# --- SYSTEM PROMPTS ---

SYSTEM_PROMPTS = {
    ModelRole.PLANNER: """You are the SnowNinja Planner — a Principal Snowflake Architect and Agent.
Your job is to understand the user's goal, explore the Snowflake environment if needed, and write a concrete execution plan.

## Your Capabilities
1. You have tools to read metadata (`list_databases`, `list_schemas`, `list_tables`, `describe_table`, `get_table_ddl`).
2. You have tools to check compute (`list_warehouses`, `get_warehouse_usage`).
3. You have tools to check security (`list_roles`, `show_grants_to`).

## Rules
1. DO NOT execute DDL or DML (no CREATE, ALTER, DROP, INSERT). You are read-only.
2. If you need to see a table's structure, use `get_table_ddl` or `describe_table`.
3. Read the injected Skill Guidance (if any). It contains critical rules you must follow.
4. When you have enough context, output a final plan.

## Output Format
When you are done planning, your FINAL message MUST end with this exact markdown section:

## Task List
- [ ] Task 1 description
- [ ] Task 2 description
""",

    ModelRole.IMPLEMENTER: """You are the SnowNinja Implementer — an expert Snowflake Data Engineer and Agent.
Your job is to execute the Task List exactly as planned.

## Your Capabilities
1. You have full workspace tools (`execute_sql`, `create_table`, `create_warehouse`, `cortex_complete`, etc).
2. You can read and write local files (`read_local_file`, `write_local_file`).

## Rules
1. You will be provided with a `## Task List` in your context.
2. Work through the tasks autonomously using your tools.
3. Validate complex SQL before executing it (`validate_sql`).
4. Read the injected Skill Guidance (if any). It contains code patterns you must use.
5. Do not stop until you hit an unrecoverable error or all tasks are complete.
"""
}

INTERVIEW_SYSTEM_PROMPT = """You are a Principal Snowflake Business Analyst.
Your job is to conduct a requirements-gathering interview with the user.

## Rules
1. Ask exactly ONE clarifying question per turn.
2. Provide 2-3 brief options (a, b, c) to make it easy for the user to answer.
3. Keep it brief. You are talking to an engineer.
4. Use Snowflake terminology correctly (Warehouses, Databases, Schemas, Roles).

When the user says "/go" or you have enough info, output the final result using EXACTLY this format:

## Requirements
(bullet points of the gathered requirements)

## Task List
- [ ] Step 1
- [ ] Step 2
"""


# --- TOOL SCHEMAS ---

SNOWFLAKE_TOOLS = [
    # Identity
    {"type": "function", "function": {"name": "get_current_user", "description": "Get current user, role, and warehouse", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "get_account_info", "description": "Get account name and region", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "list_connection_profiles", "description": "List configured Snowflake profiles", "parameters": {"type": "object", "properties": {}}}},
    
    # Metadata
    {"type": "function", "function": {"name": "list_databases", "description": "List all databases", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "list_schemas", "description": "List schemas in a database", "parameters": {"type": "object", "properties": {"database": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "list_tables", "description": "List tables in a schema", "parameters": {"type": "object", "properties": {"schema": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "describe_table", "description": "Get columns for a table", "parameters": {"type": "object", "properties": {"table_name": {"type": "string"}}, "required": ["table_name"]}}},
    {"type": "function", "function": {"name": "search_objects", "description": "Search objects by name", "parameters": {"type": "object", "properties": {"keyword": {"type": "string"}}, "required": ["keyword"]}}},
    {"type": "function", "function": {"name": "get_table_ddl", "description": "Get CREATE TABLE DDL", "parameters": {"type": "object", "properties": {"table_name": {"type": "string"}}, "required": ["table_name"]}}},
    
    # SQL
    {"type": "function", "function": {"name": "execute_sql", "description": "Execute a raw SQL query", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "validate_sql", "description": "Validate SQL syntax using EXPLAIN", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "get_query_history", "description": "Get recent queries", "parameters": {"type": "object", "properties": {"limit": {"type": "integer"}}, "required": []}}},
    
    # Warehouse
    {"type": "function", "function": {"name": "list_warehouses", "description": "List all warehouses", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "create_warehouse", "description": "Create a new warehouse", "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "size": {"type": "string", "enum": ["X-SMALL", "SMALL", "MEDIUM", "LARGE", "X-LARGE"]}}, "required": ["name"]}}},
    {"type": "function", "function": {"name": "resize_warehouse", "description": "Resize an existing warehouse", "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "size": {"type": "string"}}, "required": ["name", "size"]}}},
    {"type": "function", "function": {"name": "suspend_warehouse", "description": "Suspend a warehouse", "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}},
    
    # Data Eng
    {"type": "function", "function": {"name": "create_database", "description": "Create a database", "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}},
    {"type": "function", "function": {"name": "create_schema", "description": "Create a schema", "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}},
    {"type": "function", "function": {"name": "create_table", "description": "Create a table", "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "columns": {"type": "string"}}, "required": ["name", "columns"]}}},
    {"type": "function", "function": {"name": "drop_object", "description": "Drop an object", "parameters": {"type": "object", "properties": {"object_type": {"type": "string"}, "name": {"type": "string"}}, "required": ["object_type", "name"]}}},
    {"type": "function", "function": {"name": "list_stages", "description": "List stages", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "list_tasks", "description": "List tasks", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "list_streams", "description": "List streams", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "list_pipes", "description": "List snowpipes", "parameters": {"type": "object", "properties": {}}}},
    
    # Cortex AI
    {"type": "function", "function": {"name": "cortex_complete", "description": "Call Cortex LLM completion", "parameters": {"type": "object", "properties": {"model": {"type": "string"}, "prompt": {"type": "string"}}, "required": ["model", "prompt"]}}},
    {"type": "function", "function": {"name": "cortex_summarize", "description": "Summarize text with Cortex", "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "cortex_sentiment", "description": "Get sentiment score", "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "cortex_classify", "description": "Classify text into categories", "parameters": {"type": "object", "properties": {"text": {"type": "string"}, "categories": {"type": "array", "items": {"type": "string"}}}, "required": ["text", "categories"]}}},
    
    # Governance
    {"type": "function", "function": {"name": "list_roles", "description": "List roles", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "show_grants_on", "description": "Show grants on object", "parameters": {"type": "object", "properties": {"object_type": {"type": "string"}, "object_name": {"type": "string"}}, "required": ["object_type", "object_name"]}}},
    {"type": "function", "function": {"name": "show_grants_to", "description": "Show grants to role", "parameters": {"type": "object", "properties": {"role_name": {"type": "string"}}, "required": ["role_name"]}}},
    {"type": "function", "function": {"name": "list_tags", "description": "List tags", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "list_masking_policies", "description": "List masking policies", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "list_row_access_policies", "description": "List row access policies", "parameters": {"type": "object", "properties": {}}}},
    
    # Cost
    {"type": "function", "function": {"name": "get_warehouse_usage", "description": "Get warehouse credit usage", "parameters": {"type": "object", "properties": {"days": {"type": "integer"}}, "required": []}}},
    {"type": "function", "function": {"name": "get_storage_usage", "description": "Get storage byte usage", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "get_login_history", "description": "Get login history", "parameters": {"type": "object", "properties": {"limit": {"type": "integer"}}, "required": []}}},
    
    # Local
    {"type": "function", "function": {"name": "write_local_file", "description": "Write text to local file", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}, "content": {"type": "string"}, "overwrite": {"type": "boolean"}}, "required": ["file_path", "content"]}}},
    {"type": "function", "function": {"name": "read_local_file", "description": "Read text from local file", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}}, "required": ["file_path"]}}},
    {"type": "function", "function": {"name": "run_shell_command", "description": "Run safe shell command (ls, echo, pwd, git)", "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
]

TOOL_DISPATCH = {
    "get_current_user": lambda a: tools.get_current_user(**a),
    "get_account_info": lambda a: tools.get_account_info(**a),
    "list_connection_profiles": lambda a: tools.list_connection_profiles(**a),
    "list_databases": lambda a: tools.list_databases(**a),
    "list_schemas": lambda a: tools.list_schemas(**a),
    "list_tables": lambda a: tools.list_tables(**a),
    "describe_table": lambda a: tools.describe_table(**a),
    "search_objects": lambda a: tools.search_objects(**a),
    "get_table_ddl": lambda a: tools.get_table_ddl(**a),
    "execute_sql": lambda a: tools.execute_sql(**a),
    "validate_sql": lambda a: tools.validate_sql(**a),
    "get_query_history": lambda a: tools.get_query_history(**a),
    "list_warehouses": lambda a: tools.list_warehouses(**a),
    "create_warehouse": lambda a: tools.create_warehouse(**a),
    "resize_warehouse": lambda a: tools.resize_warehouse(**a),
    "suspend_warehouse": lambda a: tools.suspend_warehouse(**a),
    "create_database": lambda a: tools.create_database(**a),
    "create_schema": lambda a: tools.create_schema(**a),
    "create_table": lambda a: tools.create_table(**a),
    "drop_object": lambda a: tools.drop_object(**a),
    "list_stages": lambda a: tools.list_stages(**a),
    "list_tasks": lambda a: tools.list_tasks(**a),
    "list_streams": lambda a: tools.list_streams(**a),
    "list_pipes": lambda a: tools.list_pipes(**a),
    "cortex_complete": lambda a: tools.cortex_complete(**a),
    "cortex_summarize": lambda a: tools.cortex_summarize(**a),
    "cortex_sentiment": lambda a: tools.cortex_sentiment(**a),
    "cortex_classify": lambda a: tools.cortex_classify(**a),
    "list_roles": lambda a: tools.list_roles(**a),
    "show_grants_on": lambda a: tools.show_grants_on(**a),
    "show_grants_to": lambda a: tools.show_grants_to(**a),
    "list_tags": lambda a: tools.list_tags(**a),
    "list_masking_policies": lambda a: tools.list_masking_policies(**a),
    "list_row_access_policies": lambda a: tools.list_row_access_policies(**a),
    "get_warehouse_usage": lambda a: tools.get_warehouse_usage(**a),
    "get_storage_usage": lambda a: tools.get_storage_usage(**a),
    "get_login_history": lambda a: tools.get_login_history(**a),
    "write_local_file": lambda a: tools.write_local_file(**a),
    "read_local_file": lambda a: tools.read_local_file(**a),
    "run_shell_command": lambda a: tools.run_shell_command(**a),
}

# --- NIM CLIENT ---

class NimClient:
    def __init__(self):
        self._get_client()
        # Persistent history separated by role lane
        self._histories: Dict[ModelRole, List[ChatCompletionMessageParam]] = {
            ModelRole.PLANNER: [],
            ModelRole.IMPLEMENTER: []
        }
        self._interview_history: List[ChatCompletionMessageParam] = []

    def _get_client(self):
        pat = session.config.nvidia_pat or "dummy_key_to_prevent_crash"
        return AsyncOpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=pat
        )

    def _get_model_for_role(self, role: ModelRole) -> str:
        if role == ModelRole.PLANNER:
            return session.config.planner_model
        return session.config.implementer_model

    def reset_history(self, role: Optional[ModelRole] = None) -> None:
        if role:
            self._histories[role] = []
        else:
            self._histories = {ModelRole.PLANNER: [], ModelRole.IMPLEMENTER: []}
        self._interview_history = []

    def reset_interview(self) -> None:
        self._interview_history = []

    def _build_system_prompt(self, role: ModelRole) -> str:
        base = SYSTEM_PROMPTS[role]
        
        # Inject task list context for the implementer
        if role == ModelRole.IMPLEMENTER:
            if session.requirements:
                base += f"\n\n## Current Requirements\n{session.requirements}"
            if session.task_list:
                base += f"\n\n## Current Task List\n{session.task_list}"
                
        return base

    async def _execute_tool(self, name: str, args: Dict[str, Any]) -> str:
        if name not in TOOL_DISPATCH:
            return json.dumps({"status": "error", "message": f"Tool '{name}' not found."})
        
        func = TOOL_DISPATCH[name]
        try:
            result = await asyncio.to_thread(func, args)
            if isinstance(result, str):
                return result
            return json.dumps(result, default=str)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e), "traceback": traceback.format_exc()})

    async def _resolve_model(self, requested_model: str, role: ModelRole) -> str:
        """
        Probe the NIM API to see if the requested model is alive.
        If it fails, fall back to standard reliable models.
        """
        client = self._get_client()
        fallbacks = [
            NimModel.MISTRAL_LATEST.value,
            NimModel.QWEN_CODER_LATEST.value,
            NimModel.DEEPSEEK_V4.value
        ]
        
        chain = [requested_model] + [m for m in fallbacks if m != requested_model]
        
        for model in chain:
            try:
                # Fast probe
                await client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "ping"}],
                    max_tokens=1,
                    timeout=5.0
                )
                return model
            except Exception as e:
                logger.warning(f"Model probe failed for {model}: {e}")
                continue
                
        # If all fail, just return the requested one and let the real call fail loudly
        return requested_model

    def _should_fallback(self, error: Exception) -> bool:
        """Determine if an API error warrants triggering the fallback chain."""
        err_str = str(error).lower()
        # Fall back on capacity, 404s, or specific NIM gateway errors
        return any(flag in err_str for flag in ["404", "capacity", "rate limit", "503", "timeout"])

    async def agent_chat(self, prompt: str, role: ModelRole = ModelRole.PLANNER) -> AsyncGenerator[Tuple[str, Any], None]:
        client = self._get_client()
        requested_model = self._get_model_for_role(role)
        
        # 1. Resolve alive model
        model = await self._resolve_model(requested_model, role)
        if model != requested_model:
            yield "model_switch", model
            
        # 2. Skill Routing (Ephemeral)
        matched_skills = skill_router.route(prompt)
        skill_context = ""
        if matched_skills:
            yield "skill_match", matched_skills
            if role == ModelRole.PLANNER:
                skill_context = skill_router.format_for_planner(matched_skills)
            else:
                skill_context = skill_router.format_for_implementer(matched_skills)
        else:
            skill_context = f"\n\n--- SKILL INDEX ---\n{skill_router.skill_index()}\n--- END INDEX ---"

        # 3. Build Messages
        sys_prompt = self._build_system_prompt(role)
        
        # Ephemeral system message containing dynamic context (task list, skills)
        ephemeral_sys = {"role": "system", "content": sys_prompt}
        if skill_context:
            ephemeral_sys["content"] += f"\n\n{skill_context}"

        # Add user prompt to persistent history
        self._histories[role].append({"role": "user", "content": prompt})

        # Max 20 tool-calling iterations to prevent infinite loops
        for iteration in range(20):
            # Rebuild messages for this iteration: ephemeral sys + persistent history
            messages = [ephemeral_sys] + self._histories[role]
            
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
                
            except Exception as e:
                if self._should_fallback(e):
                    # Try hard fallback to Mistral Large 3
                    model = NimModel.MISTRAL_LATEST.value
                    yield "model_switch", model
                    try:
                        kwargs["model"] = model
                        response = await client.chat.completions.create(**kwargs)
                        response_msg = response.choices[0].message
                    except Exception as e2:
                        yield "error", f"Fallback model also failed: {e2}"
                        return
                else:
                    yield "error", f"API Error: {e}"
                    return

            # Append assistant response to history
            self._histories[role].append(response_msg)

            # Check if there are tool calls
            if hasattr(response_msg, "tool_calls") and response_msg.tool_calls:
                for tool_call in response_msg.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        tool_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        tool_args = {}
                    
                    yield "tool_call", (tool_name, tool_args)
                    tool_result = await self._execute_tool(tool_name, tool_args)
                    yield "tool_result", tool_result
                    
                    self._histories[role].append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": tool_name,
                        "content": tool_result
                    })
            else:
                # No more tool calls, return final response
                final_text = response_msg.content or ""
                yield "text", final_text
                return
                
        yield "error", "Exceeded maximum tool iterations (20)."

    async def interview_chat(self, user_input: str, force_finalize: bool = False) -> AsyncGenerator[Tuple[str, Any], None]:
        client = self._get_client()
        requested_model = self._get_model_for_role(ModelRole.PLANNER)
        
        # Resolve model with fallbacks
        model = await self._resolve_model(requested_model, ModelRole.PLANNER)
        if model != requested_model:
            yield "model_switch", model
        
        # Initialize history with system prompt and skills on first turn
        if not self._interview_history:
            matched_skills = skill_router.route(user_input)
            skill_block = skill_router.format_for_planner(matched_skills) if matched_skills else ""
            
            system_content = INTERVIEW_SYSTEM_PROMPT
            if skill_block:
                system_content += (
                    f"\n\n--- SKILL CONTEXT (use to ask domain-relevant questions) ---\n"
                    f"{skill_block}\n"
                    f"--- END SKILL CONTEXT ---"
                )
            self._interview_history = [{"role": "system", "content": system_content}]
        
        if force_finalize:
            self._interview_history.append({"role": "user", "content": "Please generate the Requirements and Task List now based on everything we've discussed. Output the ## Requirements and ## Task List sections exactly as specified."})
        else:
            self._interview_history.append({"role": "user", "content": user_input})
            
        # We don't prepend sys_msg here anymore because it's at index 0 of _interview_history
        messages = self._interview_history
        
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7
            )
            content = response.choices[0].message.content or ""
            self._interview_history.append({"role": "assistant", "content": content})
            
            if "## Requirements" in content and "## Task List" in content:
                yield "interview_complete", content
            elif "REQUIREMENTS_GATHERED" in content: # Fallback legacy check
                yield "interview_ready", content.replace("REQUIREMENTS_GATHERED", "").strip()
            else:
                yield "text", content
                
        except Exception as e:
            yield "error", f"Error during interview: {e}"

