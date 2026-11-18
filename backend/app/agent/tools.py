"""Tool definitions and execution handlers for ShopEasy support bot.

Enforces Security Rule #8 & #9:
- All SQL queries use bound parameters (never string formatting).
- Permission checks live in code and SQL: `WHERE id = :order_id AND user_id = :user_id`.
- The user_id is injected from the authenticated session, NEVER trusted to the LLM.
- Input arguments are validated and sanitized in code.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.order import Order
from app.rag.hybrid import hybrid_search
from app.rag.rerank import rerank_chunks
from app.rag.retrieve import retrieve_chunks


def search_docs(query: str, top_k: int = 3) -> Dict[str, Any]:
    """Search ShopEasy policy documents using hybrid search (pgvector + full-text RRF).

    Args:
        query: Customer query or policy topic to search.
        top_k: Number of chunks to retrieve.

    Returns:
        Dict with search results, sources, and concatenated text.
    """
    clean_query = str(query).strip()
    if not clean_query:
        return {"found": False, "sources": [], "content": "Empty search query provided."}

    candidates = hybrid_search(clean_query, top_k=15)
    chunks = rerank_chunks(clean_query, candidates, top_k=top_k)
    if not chunks:
        return {
            "found": False,
            "query": clean_query,
            "sources": [],
            "content": "No relevant policy documents found matching this query.",
        }

    sources = list(dict.fromkeys(c.source for c in chunks))
    content_lines = []
    for idx, c in enumerate(chunks, 1):
        content_lines.append(f"[{idx}] Source: {c.source}\n{c.chunk_text}")

    return {
        "found": True,
        "query": clean_query,
        "sources": sources,
        "content": "\n\n".join(content_lines),
    }


def get_order_status(order_id: str, user_id: str, db: Optional[Session] = None) -> Dict[str, Any]:
    """Look up order details and status for an authenticated customer.

    Security:
        Enforces `WHERE id = :order_id AND user_id = :user_id`.
        A customer can only ever view their own orders.

    Args:
        order_id: The order ID (e.g. 'A1001', 'A1002').
        user_id: The authenticated customer ID (injected from auth context).
        db: Optional database session.

    Returns:
        Dict with order details or a not-found message.
    """
    clean_order_id = str(order_id).strip().upper()
    clean_user_id = str(user_id).strip().lower()

    if not clean_order_id:
        return {"found": False, "error": "Order ID cannot be empty."}

    session = db or SessionLocal()
    try:
        stmt = select(Order).where(
            Order.id == clean_order_id,
            Order.user_id == clean_user_id,
        )
        order = session.execute(stmt).scalar_one_or_none()

        if not order:
            return {
                "found": False,
                "order_id": clean_order_id,
                "error": f"No order found with ID '{clean_order_id}' for your account.",
            }

        return {
            "found": True,
            "order_id": order.id,
            "user_id": order.user_id,
            "item": order.item,
            "price": order.price,
            "status": order.status,
            "city": order.city,
            "eta_days": order.eta_days,
            "can_cancel": order.status == "processing",
            "message": (
                f"Order {order.id} ({order.item}) is currently '{order.status}'. "
                f"Amount: ₹{order.price}. City: {order.city}."
            ),
        }
    finally:
        if not db:
            session.close()


def list_user_orders(user_id: str, limit: int = 5, db: Optional[Session] = None) -> Dict[str, Any]:
    """List recent orders belonging to the authenticated customer.

    Security:
        Enforces `WHERE user_id = :user_id`.

    Args:
        user_id: Authenticated customer ID.
        limit: Max number of orders to return.
        db: Optional database session.
    """
    clean_user_id = str(user_id).strip().lower()
    session = db or SessionLocal()
    try:
        stmt = (
            select(Order)
            .where(Order.user_id == clean_user_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        orders = session.execute(stmt).scalars().all()

        if not orders:
            return {"count": 0, "orders": [], "message": "You currently have no orders on file."}

        order_list = [
            {
                "order_id": o.id,
                "item": o.item,
                "price": o.price,
                "status": o.status,
                "city": o.city,
                "eta_days": o.eta_days,
                "can_cancel": o.status == "processing",
            }
            for o in orders
        ]
        return {
            "count": len(order_list),
            "orders": order_list,
        }
    finally:
        if not db:
            session.close()


def cancel_order(order_id: str, user_id: str, db: Optional[Session] = None) -> Dict[str, Any]:
    """Validate cancellation eligibility for an authenticated customer's order.

    ShopEasy Policy:
        - Orders can ONLY be cancelled while their status is 'processing'.
        - Once 'shipped' or 'delivered', they cannot be cancelled.
        - Cancelled orders are refunded within 3-5 business days.

    Args:
        order_id: Order ID to cancel.
        user_id: Authenticated customer ID.
        db: Optional database session.

    Returns:
        Dict indicating eligibility and next confirmation step.
    """
    clean_order_id = str(order_id).strip().upper()
    clean_user_id = str(user_id).strip().lower()

    session = db or SessionLocal()
    try:
        stmt = select(Order).where(
            Order.id == clean_order_id,
            Order.user_id == clean_user_id,
        )
        order = session.execute(stmt).scalar_one_or_none()

        if not order:
            return {
                "success": False,
                "order_id": clean_order_id,
                "error": f"No order with ID '{clean_order_id}' was found for your account.",
            }

        # Check policy eligibility
        if order.status != "processing":
            return {
                "success": False,
                "order_id": order.id,
                "item": order.item,
                "status": order.status,
                "error": (
                    f"Order {order.id} ({order.item}) cannot be cancelled because its status is '{order.status}'. "
                    "According to ShopEasy policy, orders can only be cancelled while in 'processing' status. "
                    "Once shipped or delivered, you may start a return or refuse delivery."
                ),
            }

        # Order is eligible for cancellation
        return {
            "success": True,
            "order_id": order.id,
            "item": order.item,
            "price": order.price,
            "status": "processing",
            "cancellation_status": "pending_confirmation",
            "requires_approval": True,
            "message": (
                f"Order {order.id} ({order.item}) is eligible for cancellation. "
                f"A refund of ₹{order.price} will be processed within 3-5 business days upon your confirmation."
            ),
        }
    finally:
        if not db:
            session.close()


def execute_order_cancellation(
    order_id: str, user_id: str, db: Optional[Session] = None
) -> Dict[str, Any]:
    """Actually update the order status to 'cancelled' in the database.

    Called ONLY when the customer confirms the cancellation in the approval flow.
    """
    clean_order_id = str(order_id).strip().upper()
    clean_user_id = str(user_id).strip().lower()

    session = db or SessionLocal()
    try:
        stmt = select(Order).where(
            Order.id == clean_order_id,
            Order.user_id == clean_user_id,
        )
        order = session.execute(stmt).scalar_one_or_none()

        if not order:
            return {"success": False, "error": f"Order '{clean_order_id}' not found."}

        if order.status != "processing":
            return {
                "success": False,
                "error": f"Order {order.id} cannot be cancelled (current status: '{order.status}').",
            }

        order.status = "cancelled"
        session.commit()

        return {
            "success": True,
            "order_id": order.id,
            "item": order.item,
            "price": order.price,
            "status": "cancelled",
            "message": f"Order {order.id} ({order.item}) has been successfully cancelled. Refund of ₹{order.price} will arrive in 3-5 business days.",
        }
    finally:
        if not db:
            session.close()


# Tool specifications (JSON Schema) for the LLM Tool Call Registry
TOOL_DEFINITIONS = [
    {
        "name": "search_docs",
        "description": "Search ShopEasy customer support policies (returns, refunds, shipping, warranty, membership, payment errors).",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The policy search query (e.g. 'earbuds return window', 'express delivery cities').",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_order_status",
        "description": "Look up details, tracking, item name, amount, and current status for a specific customer order ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID to check (e.g. 'A1001', 'A1002').",
                }
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "list_user_orders",
        "description": "List recent orders placed by the currently logged-in customer.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of recent orders to retrieve (default: 5).",
                }
            },
        },
    },
    {
        "name": "cancel_order",
        "description": "Request cancellation of an order. Orders can only be cancelled if they are in 'processing' status.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID to cancel (e.g. 'A1002').",
                }
            },
            "required": ["order_id"],
        },
    },
]
