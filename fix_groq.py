import pathlib
code = r'''
import os, json, re
from groq import Groq
from langchain_core.messages import AIMessage, HumanMessage
from agent.state import (AgentState, LeadInfo, INTENT_GREETING, INTENT_PRODUCT_INQUIRY,
    INTENT_HIGH_INTENT, INTENT_PROVIDE_INFO, INTENT_OTHER, ALL_LEAD_FIELDS)
from agent.rag import retrieve_context, get_full_kb
from agent.tools import mock_lead_capture, validate_email, extract_lead_fields_from_text

_client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))

def _llm(system, messages, max_tokens=512):
    fmt = [{"role": "system", "content": system}]
    for m in messages:
        if isinstance(m, HumanMessage):
            fmt.append({"role": "user", "content": m.content})
        elif isinstance(m, AIMessage):
            fmt.append({"role": "assistant", "content": m.content})
        elif isinstance(m, dict):
            fmt.append({"role": m.get("role", "user"), "content": m.get("content", "")})
    if len(fmt) == 1:
        fmt.append({"role": "user", "content": "Hello"})
    resp = _client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=fmt,
        max_tokens=max_tokens
    )
    return resp.choices[0].message.content.strip()

def classify_intent(state: AgentState) -> dict:
    msgs = state["messages"]
    last = next((m.content for m in reversed(msgs) if isinstance(m, HumanMessage)), "")
    lead_info = state.get("lead_info", {})
    pending = state.get("pending_fields", ALL_LEAD_FIELDS[:])
    lo = last.lower()
    if any(w in lo for w in ["hi","hello","hey","howdy"]):
        return {"intent": INTENT_GREETING}
    if any(w in lo for w in ["sign up","buy","try","subscribe","want to","i want","ready","interested"]):
        return {"intent": INTENT_HIGH_INTENT}
    if any(w in lo for w in ["price","plan","feature","cost","refund","support","4k","caption","policy"]):
        return {"intent": INTENT_PRODUCT_INQUIRY}
    extracted = extract_lead_fields_from_text(last, lead_info)
    if extracted != lead_info or "@" in last:
        return {"intent": INTENT_PROVIDE_INFO}
    if pending:
        return {"intent": INTENT_PROVIDE_INFO}
    return {"intent": INTENT_OTHER}

def retrieve_rag(state: AgentState) -> dict:
    msgs = state["messages"]
    last = next((m.content for m in reversed(msgs) if isinstance(m, HumanMessage)), "")
    if state.get("intent") == INTENT_GREETING:
        return {"rag_context": None}
    return {"rag_context": retrieve_context(last)}

def generate_response(state: AgentState) -> dict:
    msgs = state["messages"]
    intent = state.get("intent", INTENT_OTHER)
    kb = state.get("rag_context") or get_full_kb()
    lead_info = state.get("lead_info", {})
    pending = state.get("pending_fields", ALL_LEAD_FIELDS[:])
    captured = state.get("lead_captured", False)
    field_labels = {"name": "full name", "email": "email address", "platform": "content platform such as YouTube or Instagram"}
    system = "You are Aria, friendly AI sales assistant for AutoStream video editing SaaS. Be warm and concise. Only answer from the knowledge base below. Never ask for more than one lead field per turn.\nKnowledge Base:\n" + kb
    if intent == INTENT_HIGH_INTENT and not captured and pending:
        system += "\n\nUser wants to sign up. Ask for their " + field_labels[pending[0]] + " now."
    if intent == INTENT_PROVIDE_INFO and pending:
        if len(pending) > 1:
            system += "\n\nAcknowledge what they shared, then ask for their " + field_labels[pending[0]] + "."
        else:
            system += "\n\nAll details collected. Confirm and say the team will be in touch!"
    if captured:
        system += "\n\nLead already captured. Wrap up warmly."
    history = []
    for m in msgs:
        if isinstance(m, HumanMessage):
            history.append({"role": "user", "content": m.content})
        elif isinstance(m, AIMessage):
            history.append({"role": "assistant", "content": m.content})
    resp = _llm(system, history, 400)
    return {"messages": [AIMessage(content=resp)], "turn_count": state.get("turn_count", 0) + 1}

def collect_lead_info(state: AgentState) -> dict:
    msgs = state["messages"]
    lead_info = dict(state.get("lead_info", {}))
    last = next((m.content for m in reversed(msgs) if isinstance(m, HumanMessage)), "")
    lead_info = extract_lead_fields_from_text(last, lead_info)
    if not lead_info.get("name") and state.get("intent") == INTENT_PROVIDE_INFO:
        raw = _llm("Extract only the full name from this message. Reply with just the name or NONE.", [{"role": "user", "content": "Message: " + last}], 32)
        if raw.strip().upper() != "NONE" and len(raw.strip()) > 1:
            lead_info["name"] = raw.strip()
    pending = [f for f in ALL_LEAD_FIELDS if not lead_info.get(f)]
    return {"lead_info": LeadInfo(**lead_info), "pending_fields": pending}

def capture_lead(state: AgentState) -> dict:
    if state.get("lead_captured"): return {}
    li = state.get("lead_info", {})
    name, email, platform = li.get("name"), li.get("email"), li.get("platform")
    if not all([name, email, platform]): return {}
    if not validate_email(email): return {}
    mock_lead_capture(name=name, email=email, platform=platform)
    return {"lead_captured": True, "pending_fields": []}
'''
pathlib.Path("agent/nodes.py").write_text(code.strip(), encoding="utf-8")
print("nodes.py updated to Groq!")
