"""Query Rewriting module for multi-turn conversational customer support.

Resolves conversational pronouns, ellipses, and references from past messages
into standalone search queries before executing Hybrid Search (pgvector + FTS).
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.llm import generate_completion

REWRITE_SYSTEM_PROMPT = """You are a query rewriting assistant for a customer support search engine at ShopEasy (an electronics store).
Your task is to rewrite a customer's follow-up question into a single, self-contained search query based on the conversation history.

Rules:
1. Resolve all pronouns (it, that, they, this) and conversational follow-ups (e.g., "what about earbuds?", "is it available in Pune?", "and for laptops?").
2. The rewritten query MUST be a concise, standalone question or search phrase suitable for document search.
3. Keep the user's intent exact; DO NOT answer the question or make up policies.
4. If the latest message is ALREADY completely self-contained, return it as-is without changing it.
5. Output ONLY the rewritten query text. Do not add quotes, markdown formatting, or preamble.
"""


def rewrite_query(query: str, history: Optional[List[Dict[str, str]]] = None) -> str:
    """Rewrite a follow-up query using conversation history into a standalone query.

    Args:
        query: Customer's latest message or search query.
        history: Optional list of past messages in the format [{'role': 'user'|'assistant', 'content': '...'}]

    Returns:
        A standalone search query string.
    """
    clean_query = str(query).strip()
    if not clean_query:
        return ""

    # If there is no conversation history, query is already the initial question
    if not history or len(history) == 0:
        return clean_query

    # Format recent history (keep up to last 4 turns)
    recent_turns = history[-4:]
    dialogue_lines = []
    for msg in recent_turns:
        role = "Customer" if msg.get("role") == "user" else "Assistant"
        dialogue_lines.append(f"{role}: {msg.get('content', '')}")
    dialogue_str = "\n".join(dialogue_lines)

    prompt = (
        f"Conversation History:\n{dialogue_str}\n\n"
        f"Customer's Follow-up: {clean_query}\n\n"
        f"Rewritten Standalone Query:"
    )

    try:
        rewritten = generate_completion(
            prompt=prompt,
            system_prompt=REWRITE_SYSTEM_PROMPT,
            max_tokens=1024,
        )
        rewritten_clean = rewritten.strip().strip('"').strip("'")
        return rewritten_clean if rewritten_clean else clean_query
    except Exception as e:
        # Fall back to original query if LLM call fails
        print(f"Warning: query rewriting failed: {e}")
        return clean_query
