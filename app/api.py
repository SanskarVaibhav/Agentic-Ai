"""
app/api.py – FastAPI REST wrapper for the AutoStream Inflx Agent.

Endpoints:
  POST /chat          – Send a message, get a response (stateful per session_id)
  POST /chat/reset    – Reset a session
  GET  /session/{id}  – Get current session state (intent, lead_info, etc.)
  GET  /leads         – List all captured leads
  GET  /health        – Health check
"""

import os
import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage

# ── Import agent ──────────────────────────────────────────────────────────────
from agent.graph import build_graph
from agent.state import ALL_LEAD_FIELDS
from agent.tools import get_all_leads

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AutoStream Inflx Agent API",
    description="Social-to-Lead Agentic Workflow — converts social conversations into qualified leads.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Compile graph once at startup ─────────────────────────────────────────────
graph = build_graph()


# ── Request / Response models ─────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  # If None, a new session is created


class ChatResponse(BaseModel):
    session_id: str
    response: str
    intent: Optional[str]
    lead_captured: bool
    pending_fields: list
    lead_info: dict
    turn_count: int


class ResetRequest(BaseModel):
    session_id: str


# ── Helper ─────────────────────────────────────────────────────────────────────

def _run_turn(session_id: str, user_message: str) -> dict:
    config = {"configurable": {"thread_id": session_id}}
    existing = graph.get_state(config)

    if existing.values:
        inputs = {"messages": [HumanMessage(content=user_message)]}
    else:
        inputs = {
            "messages": [HumanMessage(content=user_message)],
            "lead_info": {},
            "pending_fields": ALL_LEAD_FIELDS[:],
            "lead_captured": False,
            "rag_context": None,
            "turn_count": 0,
        }

    final = None
    for chunk in graph.stream(inputs, config=config, stream_mode="values"):
        final = chunk

    ai_response = ""
    if final and "messages" in final:
        for m in reversed(final["messages"]):
            if isinstance(m, AIMessage):
                ai_response = m.content
                break

    return {
        "response": ai_response,
        "intent": final.get("intent") if final else None,
        "lead_captured": final.get("lead_captured", False) if final else False,
        "pending_fields": final.get("pending_fields", []) if final else [],
        "lead_info": dict(final.get("lead_info", {})) if final else {},
        "turn_count": final.get("turn_count", 0) if final else 0,
    }


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "AutoStream Inflx Agent API", "version": "1.0.0"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    Send a message to the AutoStream AI agent.

    - If no session_id is provided, a new session is automatically created.
    - State (conversation history, lead info) persists across calls with the same session_id.
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    session_id = req.session_id or str(uuid.uuid4())

    result = _run_turn(session_id, req.message)

    return ChatResponse(session_id=session_id, **result)


@app.post("/chat/reset")
def reset_session(req: ResetRequest):
    """
    Reset a conversation session. Clears all state including lead info.
    The same session_id can then be reused for a fresh conversation.
    """
    # LangGraph MemorySaver: delete checkpoint by overwriting with empty state
    config = {"configurable": {"thread_id": req.session_id}}
    existing = graph.get_state(config)
    if not existing.values:
        raise HTTPException(status_code=404, detail=f"Session '{req.session_id}' not found.")

    # Write blank state to effectively reset
    graph.update_state(config, {
        "lead_info": {},
        "pending_fields": ALL_LEAD_FIELDS[:],
        "lead_captured": False,
        "rag_context": None,
        "turn_count": 0,
    })

    return {"status": "reset", "session_id": req.session_id}


@app.get("/session/{session_id}")
def get_session(session_id: str):
    """
    Retrieve the current state of a conversation session.
    Useful for debugging or displaying session context in a UI.
    """
    config = {"configurable": {"thread_id": session_id}}
    state = graph.get_state(config)

    if not state.values:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    messages = []
    for m in state.values.get("messages", []):
        if isinstance(m, HumanMessage):
            messages.append({"role": "user", "content": m.content})
        elif isinstance(m, AIMessage):
            messages.append({"role": "assistant", "content": m.content})

    return {
        "session_id": session_id,
        "intent": state.values.get("intent"),
        "lead_captured": state.values.get("lead_captured", False),
        "lead_info": dict(state.values.get("lead_info", {})),
        "pending_fields": state.values.get("pending_fields", []),
        "turn_count": state.values.get("turn_count", 0),
        "message_count": len(messages),
        "messages": messages,
    }


@app.get("/leads")
def list_leads():
    """
    Returns all leads captured during this server session.
    In production, this would query your CRM or database.
    """
    leads = get_all_leads()
    return {
        "total": len(leads),
        "leads": leads,
    }
