# 🎬 AutoStream × Inflx — Social-to-Lead Agentic Workflow

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![LangGraph](https://img.shields.io/badge/LangGraph-1.0-purple?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136-green?style=for-the-badge&logo=fastapi)
![Groq](https://img.shields.io/badge/Groq-Llama_3.1-orange?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**An AI-powered conversational agent that converts social media conversations into qualified business leads.**

*Machine Learning Intern Assignment | ServiceHive | Product: Inflx*

</div>

---

## 📌 Overview

**AutoStream** is a fictional SaaS company offering automated video editing tools for content creators. This project builds a production-grade **Social-to-Lead Agentic Workflow** for AutoStream using LangGraph, FastAPI, and Groq (Llama 3.1).

The agent — named **Aria** — can:
- Understand and classify user intent in real time
- Answer product questions accurately using RAG from a local knowledge base
- Detect high-intent users ready to sign up
- Progressively collect lead information (name, email, platform)
- Trigger a mock CRM API only after all lead fields are validated

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    LangGraph Agent Pipeline                      │
│                                                                  │
│   User Message                                                   │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────────┐                                            │
│  │ classify_intent  │ ──── greeting / product_inquiry /          │
│  └────────┬────────┘       high_intent / provide_info           │
│           │                                                      │
│       ▼                                                          │
│  ┌─────────────────┐                                            │
│  │  retrieve_rag   │ ──── keyword match → JSON knowledge base   │
│  └────────┬────────┘                                            │
│           │                                                      │
│       ▼                                                          │
│  ┌─────────────────┐                                            │
│  │collect_lead_info│ ──── regex + LLM extraction                │
│  └────────┬────────┘                                            │
│           │                                                      │
│    ┌──────┴──────┐                                              │
│    │  Conditional │                                              │
│    │    Edge      │                                              │
│    └──┬───────┬──┘                                              │
│       │       │                                                  │
│  All fields   │ Fields missing                                   │
│  collected    │                                                  │
│       ▼       ▼                                                  │
│  ┌──────────┐ ┌──────────────────┐                             │
│  │capture_  │ │ generate_response│                             │
│  │  lead    │ │   (Groq LLM)     │                             │
│  └────┬─────┘ └──────────────────┘                             │
│       │                                                          │
│       ▼                                                          │
│  ┌──────────────────┐                                           │
│  │ generate_response│ ──── warm confirmation message            │
│  └──────────────────┘                                           │
└─────────────────────────────────────────────────────────────────┘
```

### Why LangGraph?

LangGraph was chosen over AutoGen because it provides **explicit, auditable control flow** via a directed graph. The conditional edge structurally prevents `mock_lead_capture()` from firing until all three lead fields are collected and validated — this is enforced at the graph level, not just by prompt instructions.

### State Management

State is defined as a `TypedDict` (`AgentState`) containing full message history, detected intent, progressively collected lead fields, a `lead_captured` flag, and turn count. LangGraph's `MemorySaver` checkpointer persists this state per `thread_id`, giving the agent complete memory across 5–6+ conversation turns.

---

## 📁 Project Structure

```
ML-Project/
├── agent/
│   ├── __init__.py          # Package entry point
│   ├── state.py             # AgentState TypedDict + intent constants
│   ├── rag.py               # RAG pipeline — keyword retrieval from JSON KB
│   ├── nodes.py             # 5 LangGraph node implementations
│   ├── graph.py             # Graph construction & compilation
│   └── tools.py             # mock_lead_capture() + validation helpers
├── app/
│   ├── __init__.py
│   └── api.py               # FastAPI REST server (5 endpoints)
├── knowledge_base/
│   └── autostream_kb.json   # Pricing, plans, policies, FAQs
├── postman/
│   └── AutoStream_Inflx_Agent.postman_collection.json
├── main.py                  # CLI entry point (interactive + --demo mode)
├── requirements.txt
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- A free [Groq API key](https://console.groq.com) (no credit card required)

### Installation

```bash
# Clone the repository
git clone https://github.com/SanskarVaibhav/ML-Project.git
cd ML-Project

# Install dependencies
pip install -r requirements.txt
```

### Set API Key

```bash
# Windows PowerShell
$env:GROQ_API_KEY="gsk_your_key_here"

# macOS / Linux
export GROQ_API_KEY="gsk_your_key_here"
```

### Run the API Server

```bash
python -m uvicorn app.api:app --reload --port 8000
```

### Run CLI (Interactive Mode)

```bash
python main.py
```

### Run Demo Scenario

```bash
python main.py --demo
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/chat` | Send a message (stateful per session_id) |
| `POST` | `/chat/reset` | Reset a conversation session |
| `GET` | `/session/{id}` | Inspect session state |
| `GET` | `/leads` | List all captured leads |

### Example Request

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hi, tell me about your Pro plan"}'
```

### Example Response

```json
{
  "session_id": "abc-123-xyz",
  "response": "Hi! AutoStream's Pro Plan is $79/month and includes unlimited videos, 4K exports, AI captions in 30+ languages, and 24/7 priority support. Would you like to get started?",
  "intent": "product_inquiry",
  "lead_captured": false,
  "pending_fields": ["name", "email", "platform"],
  "lead_info": {},
  "turn_count": 1
}
```

---

## 🤖 Agent Capabilities

### 1. Intent Classification

The agent classifies every message into one of five intents:

| Intent | Trigger Examples |
|--------|-----------------|
| `greeting` | "Hi", "Hello", "Hey" |
| `product_inquiry` | "What's the price?", "Tell me about features" |
| `high_intent` | "I want to sign up", "I'm ready to try" |
| `provide_info` | "My name is Alex", "alex@gmail.com" |
| `other` | Anything else |

### 2. RAG-Powered Knowledge Retrieval

The knowledge base (`autostream_kb.json`) contains:
- **Pricing Plans** — Basic ($29/mo) and Pro ($79/mo) with full feature lists
- **Company Policies** — Refund, support, cancellation, free trial
- **FAQs** — Platform support, security, upgrades

Keyword-based retrieval matches user queries to relevant KB sections and injects the context into the LLM system prompt, ensuring factually grounded responses.

### 3. Progressive Lead Collection

The agent collects lead fields **one at a time** in this order:
1. Full Name
2. Email Address (with regex validation)
3. Content Platform (YouTube, Instagram, TikTok, etc.)

The `mock_lead_capture()` tool fires **only** when all three fields are collected and validated — enforced by a conditional graph edge, not just prompt logic.

### 4. Tool Execution (mock_lead_capture)

```python
def mock_lead_capture(name: str, email: str, platform: str) -> dict:
    # Simulates CRM API call
    # In production: POST to HubSpot / Salesforce / Zoho
    print(f"Lead captured successfully: {name}, {email}, {platform}")
    return {"success": True, "lead_id": "LEAD-1001"}
```

---

## 💬 Sample Conversation

```
You:  Hi! I'm looking for a video editing tool for my YouTube channel.
Aria: Hey there! Welcome to AutoStream 🎬 We're an AI-powered video editing
      platform built for creators like you. What would you like to know?

You:  What does the Pro plan include?
Aria: The Pro Plan ($79/month) includes:
      • Unlimited videos per month
      • 4K resolution exports
      • AI-powered auto-captions in 30+ languages
      • Priority 24/7 live support
      • 100 GB cloud storage
      Would you like to get started?

You:  Yes! I want to sign up.
Aria: Amazing! Let's get you set up. Could I start with your full name?

You:  Alex Rivera
Aria: Great, Alex! What's your email address?

You:  alex.rivera@gmail.com
Aria: Perfect! And which platform do you mainly create on?

You:  YouTube
Aria: You're all set, Alex! 🎉 The AutoStream team will reach out to
      alex.rivera@gmail.com shortly. Welcome aboard!

# Terminal output:
# ============================================================
# LEAD CAPTURED SUCCESSFULLY
# ============================================================
#   Lead captured successfully: Alex Rivera, alex.rivera@gmail.com, Youtube
#   Lead ID  : LEAD-1001
#   Timestamp: 2026-04-24T05:48:10Z
# ============================================================
```

---

## 📮 Postman Collection

Import `postman/AutoStream_Inflx_Agent.postman_collection.json` into Postman to run the full demo flow with 11 pre-configured requests and automated test scripts.

**Run order:** 1 → 2 → 3 → 4 → 5 → 6 → 7 → **8 (triggers lead capture)** → 9 → 10

---

## 📱 WhatsApp Deployment via Webhooks

To deploy this agent on WhatsApp using the Meta Business Cloud API:

```
User (WhatsApp)
    │
    ▼
Meta WhatsApp Cloud API
    │  HTTP POST to webhook
    ▼
FastAPI Webhook Server
    │  phone_number used as thread_id
    ▼
LangGraph Agent (this codebase)
    │  state persisted per phone number
    ▼
WhatsApp API — sends reply
```

**Implementation:**

```python
@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    data = await request.json()
    message = data["entry"][0]["changes"][0]["value"]["messages"][0]
    phone   = message["from"]          # used as thread_id
    text    = message["text"]["body"]

    response, _ = run_chat(graph, thread_id=phone, user_input=text)
    await send_whatsapp_message(phone, response)
    return {"status": "ok"}
```

**Production checklist:**
- Replace `MemorySaver` with `langgraph-checkpoint-postgres` for persistence across restarts
- Replace `mock_lead_capture()` with real CRM API (HubSpot, Salesforce, Zoho)
- Register webhook URL in Meta Developer Console
- Each phone number = unique `thread_id` = isolated conversation state

---

## 📦 Dependencies

```
anthropic / groq          # LLM API client
langchain                 # Core LangChain abstractions
langchain-core            # Messages, runnables
langgraph                 # Graph-based agent orchestration
fastapi                   # REST API framework
uvicorn                   # ASGI server
python-dotenv             # Environment variable management
```

---

## 🧪 Evaluation Criteria Met

| Criteria | Implementation |
|----------|---------------|
| Agent reasoning & intent detection | LangGraph node + keyword fallback |
| Correct use of RAG | JSON KB → keyword retrieval → system prompt injection |
| Clean state management | `AgentState` TypedDict + `MemorySaver` per `thread_id` |
| Proper tool calling logic | Conditional edge — fires only when all fields validated |
| Code clarity & structure | 5 single-responsibility modules |
| Real-world deployability | FastAPI server + WhatsApp webhook guide |

---

## 👨‍💻 Author

**Sanskar Vaibhav**
Machine Learning Intern Assignment — ServiceHive | Inflx

---

## 📄 License

MIT License — built for the ServiceHive Inflx ML Intern Assignment.
