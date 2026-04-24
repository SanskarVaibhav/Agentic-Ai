import json, re
from pathlib import Path
from typing import Optional

_KB_PATH = Path(__file__).parent.parent / "knowledge_base" / "autostream_kb.json"
with open(_KB_PATH, "r") as f:
    _KB = json.load(f)

def _format_plans():
    lines = ["## AutoStream Pricing Plans\n"]
    for plan in _KB["plans"]:
        name = plan["name"]
        price = plan["price_monthly"]
        ideal = plan["ideal_for"]
        lines.append(f"### {name} - ${price}/month")
        lines.append(f"Best for: {ideal}")
        lines.append("Features:")
        for feat in plan["features"]:
            lines.append(f"  - {feat}")
        if plan["limitations"]:
            lines.append("Limitations:")
            for lim in plan["limitations"]:
                lines.append(f"  x {lim}")
        lines.append("")
    return "\n".join(lines)

def _format_policies():
    lines = ["## AutoStream Policies\n"]
    for p in _KB["policies"]:
        topic = p["topic"]
        details = p["details"]
        lines.append(f"### {topic}")
        lines.append(details)
        lines.append("")
    return "\n".join(lines)

def _format_company():
    c = _KB["company"]
    desc = c["description"]
    tag = c["tagline"]
    return f"## About AutoStream\n{desc}\nTagline: {tag}\n"

def _format_faqs():
    lines = ["## FAQs\n"]
    for faq in _KB["faqs"]:
        q = faq["question"]
        a = faq["answer"]
        lines.append(f"Q: {q}")
        lines.append(f"A: {a}")
        lines.append("")
    return "\n".join(lines)

_TRIGGERS = {
    "plan": _format_plans, "price": _format_plans, "pricing": _format_plans,
    "cost": _format_plans, "basic": _format_plans, "pro": _format_plans,
    "feature": _format_plans, "4k": _format_plans, "caption": _format_plans,
    "resolution": _format_plans, "video": _format_plans, "unlimited": _format_plans,
    "refund": _format_policies, "cancel": _format_policies, "support": _format_policies,
    "policy": _format_policies, "trial": _format_policies, "enterprise": _format_policies,
    "youtube": _format_faqs, "instagram": _format_faqs, "tiktok": _format_faqs,
    "platform": _format_faqs, "secure": _format_faqs, "upgrade": _format_faqs,
    "about": _format_company, "autostream": _format_company,
}

def retrieve_context(query: str) -> Optional[str]:
    q = query.lower()
    matched = set()
    for kw, fn in _TRIGGERS.items():
        if kw in q:
            matched.add(fn)
    if not matched:
        return None
    matched.add(_format_company)
    return "\n---\n".join(fn() for fn in matched)

def get_full_kb() -> str:
    return "\n---\n".join([_format_company(), _format_plans(), _format_policies(), _format_faqs()])
