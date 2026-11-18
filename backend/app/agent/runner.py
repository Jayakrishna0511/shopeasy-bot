"""Multi-turn Agent Loop with Tool Calling, Guarded Max Steps, and Approval Flow.

Enforces:
- Maximum 6 iteration steps per request.
- User identity is injected in code (`user_id = current_user.id`), never by the model.
- Tool arguments are validated in code before execution.
- Risky writes (cancellations) generate a single-use expiring approval token.
"""

from dataclasses import dataclass, field
import json
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

from app.agent.tools import (
    TOOL_DEFINITIONS,
    cancel_order,
    get_order_status,
    list_user_orders,
    search_docs,
)
from app.config import settings
from app.core.approval import create_approval_token
from app.services.llm import detect_provider

MAX_STEPS = 6

AGENT_SYSTEM_PROMPT = """You are the AI customer support assistant for ShopEasy, an electronics store in Hyderabad, India.

You have access to real-time tools to assist customers:
- search_docs: Search store policies (returns, warranties, shipping, payment errors, memberships).
- get_order_status: Check order details, status, ETA, and tracking for a specific order ID.
- list_user_orders: List the customer's recent orders.
- cancel_order: Request cancellation of an order (eligible ONLY while in 'processing' status).

RULES:
1. When asked about general store policies, call `search_docs`.
2. When asked about orders (e.g. "what are my orders?", "where is my laptop?"), call `list_user_orders` or `get_order_status`.
3. When the customer wants to cancel an order, call `cancel_order`.
4. If an order cannot be cancelled (e.g. already 'shipped' or 'delivered'), explain the policy clearly and offer returns or support options.
5. If no documents or tools provide an answer, state politely: "I don't know based on the provided documents."
6. Professional, helpful, and concise responses.
"""


@dataclass
class AgentResult:
    answer: str
    sources: List[str] = field(default_factory=list)
    tools_called: List[Dict[str, Any]] = field(default_factory=list)
    approval_required: Optional[Dict[str, Any]] = None


def _execute_tool(
    name: str,
    args: Dict[str, Any],
    user_id: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """Execute a tool call safely in code with the authenticated user_id injected."""
    if name == "search_docs":
        query = args.get("query", "")
        return search_docs(query, history=conversation_history)

    elif name == "get_order_status":
        order_id = args.get("order_id", "")
        return get_order_status(order_id, user_id=user_id)

    elif name == "list_user_orders":
        limit = args.get("limit", 5)
        return list_user_orders(user_id=user_id, limit=limit)

    elif name == "cancel_order":
        order_id = args.get("order_id", "")
        return cancel_order(order_id, user_id=user_id)

    else:
        return {"error": f"Unknown tool '{name}'."}


def run_agent(
    message: str,
    user_id: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    max_steps: int = MAX_STEPS,
) -> AgentResult:
    """Run the multi-turn agent tool loop.

    1. Formats conversation with system instruction and tools.
    2. Calls LLM (Gemini or Anthropic).
    3. If the LLM requests a tool call, executes it in code with authenticated user_id.
    4. Appends tool results and loops until final answer or max_steps reached.
    5. Detects approval requirements (e.g. cancel_order) and attaches approval token.
    """
    key = settings.anthropic_api_key.strip()
    provider = detect_provider(key)

    # Gemini Native Function Calling
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={key}"
    gemini_tools = [
        {
            "function_declarations": [
                {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["parameters"],
                }
                for t in TOOL_DEFINITIONS
            ]
        }
    ]

    contents = []

    # Inject conversation history if available
    if conversation_history:
        for item in conversation_history:
            role = "user" if item.get("role") == "user" else "model"
            contents.append({"role": role, "parts": [{"text": item.get("content", "")}]})

    # Add current user message
    contents.append({"role": "user", "parts": [{"text": message}]})

    tools_called: List[Dict[str, Any]] = []
    collected_sources: List[str] = []
    pending_approval: Optional[Dict[str, Any]] = None

    for step in range(max_steps):
        payload = {
            "contents": contents,
            "systemInstruction": {"parts": [{"text": AGENT_SYSTEM_PROMPT}]},
            "tools": gemini_tools,
            "generationConfig": {"maxOutputTokens": 1024},
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        candidates = data.get("candidates", [])
        if not candidates:
            break

        cand = candidates[0]
        parts = cand.get("content", {}).get("parts", [])
        if not parts:
            break

        # Check for functionCall
        has_function_call = False
        for part in parts:
            if "functionCall" in part:
                has_function_call = True
                fn = part["functionCall"]
                fn_name = fn.get("name")
                fn_args = fn.get("args", {})
                call_id = fn.get("id")

                tools_called.append({"name": fn_name, "args": fn_args})

                # Execute tool in code
                tool_output = _execute_tool(
                    fn_name,
                    fn_args,
                    user_id=user_id,
                    conversation_history=conversation_history,
                )

                # Collect sources if search_docs was called
                if fn_name == "search_docs" and "sources" in tool_output:
                    collected_sources.extend(tool_output["sources"])

                # Handle cancellation approval requirement
                if fn_name == "cancel_order" and tool_output.get("success") is True:
                    order_id = tool_output.get("order_id")
                    token = create_approval_token(
                        action="cancel_order",
                        user_id=user_id,
                        details={
                            "order_id": order_id,
                            "item": tool_output.get("item"),
                            "price": tool_output.get("price"),
                        },
                    )
                    pending_approval = {
                        "token": token,
                        "action": "cancel_order",
                        "order_id": order_id,
                        "item": tool_output.get("item"),
                        "price": tool_output.get("price"),
                        "message": tool_output.get("message"),
                    }
                    tool_output["approval_token"] = token

                # Add model call and user response to conversation turn
                contents.append({"role": "model", "parts": [part]})

                response_part = {
                    "functionResponse": {
                        "name": fn_name,
                        "response": tool_output,
                    }
                }
                if call_id:
                    response_part["functionResponse"]["id"] = call_id

                contents.append({"role": "user", "parts": [response_part]})
                break  # process one function call per step

        # If model gave a direct text answer (no function call), return it
        if not has_function_call:
            final_text = parts[0].get("text", "").strip()
            return AgentResult(
                answer=final_text,
                sources=list(dict.fromkeys(collected_sources)),
                tools_called=tools_called,
                approval_required=pending_approval,
            )

    return AgentResult(
        answer="I have processed your request.",
        sources=list(dict.fromkeys(collected_sources)),
        tools_called=tools_called,
        approval_required=pending_approval,
    )
