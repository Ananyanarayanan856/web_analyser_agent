from app.state import AgentState
from app.llm import llm
import json
import re

def intent_router_node(state: AgentState) -> AgentState:
    user_input = state["user_input"]
    existing_url = state.get("url")  # Preserve URL from form

    prompt = f"""Classify this user message into intent and analysis_types.

Reply with ONLY a raw JSON object, no explanation, no markdown, no backticks.
Use exactly this format: {{"intent": "analyze_website", "analysis_types": ["seo", "accessibility", "content"]}}

Valid intents:
- "analyze_website" -> user wants SEO, accessibility, or content analysis
- "database_query"  -> user wants to read/write/delete database records  
- "both"            -> user wants analysis AND to save/query results

Valid analysis_types (only include what the user explicitly asks for. If they ask for general analysis without specifying, include all three):
- "seo"
- "accessibility"
- "content"

If database intent only, analysis_types should be empty [].

User message: {user_input}"""

    response = llm.invoke(prompt)
    text = response.content.strip()

    # Strip markdown code fences if model wraps in ```json ... ```
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    text = text.strip()

    # Parse JSON
    try:
        parsed = json.loads(text)
    except Exception:
        match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
        try:
            parsed = json.loads(match.group()) if match else {}
        except Exception:
            parsed = {}

    # Determine intent with safe fallback
    intent = parsed.get("intent", "analyze_website")
    if intent not in ("analyze_website", "database_query", "both"):
        intent = "analyze_website"
        
    analysis_types = parsed.get("analysis_types", ["seo", "accessibility", "content"])

    # URL: keep form value; only regex-extract from input if missing
    url = existing_url
    if not url:
        url_match = re.search(r'https?://[^\s]+', user_input)
        url = url_match.group() if url_match else None

    return {
        **state,
        "intent": intent,
        "analysis_types": analysis_types,
        "url": url,
    }