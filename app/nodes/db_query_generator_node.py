from app.state import AgentState
from app.llm import llm
import json, re

def db_query_generator_node(state: AgentState) -> AgentState:
    user_input = state["user_input"]
    seo = state.get("seo_result") or {}
    acc = state.get("accessibility_result") or {}
    content = state.get("content_result") or {}

    prompt = f"""You are a SQL generator. Generate a safe SQL operation for the user's request.
Allowed tables and columns:
- websites: website_id, url, created_at, last_scanned, seo_status, accessibility_status, content_status
- seo_reports: id, url, score, grade, issues, details, created_at, updated_at
- accessibility_reports: id, url, score, grade, issues, details, created_at, updated_at
- content_reports: id, url, score, grade, word_count, readability, issues, details, created_at, updated_at
- analysis_summary: id, url, summary, created_at, updated_at
- db_logs: log_id, timestamp, operation, table_name, query, status, error_message, executed_by

Respond ONLY as JSON with keys: operation, table, sql

Context (use these values if storing results):
- URL: {state.get('url')}
- SEO result: {json.dumps(seo)}
- Accessibility result: {json.dumps(acc)}  
- Content result: {json.dumps(content)}

User request: {user_input}

Example response:
{{"operation": "INSERT", "table": "seo_reports", "sql": "INSERT INTO seo_reports (url, score, issues) VALUES ('https://example.com', 85, 'Missing meta tags')"}}"""

    response = llm.invoke(prompt)
    text = response.content.strip()
    try:
        clean_text = re.sub(r'```(?:json)?\n?|\n?```', '', text).strip()
        parsed = json.loads(clean_text)
    except Exception:
        try:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            parsed = json.loads(match.group()) if match else {}
        except:
            parsed = {}

    return {**state, "db_query": json.dumps(parsed)}