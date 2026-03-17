from app.state import AgentState
import json

def response_formatter_node(state: AgentState) -> AgentState:
    context = {}
    if state.get("seo_result"): context["seo_result"] = state["seo_result"]
    if state.get("accessibility_result"): context["accessibility_result"] = state["accessibility_result"]
    if state.get("content_result"): context["content_result"] = state["content_result"]
    if state.get("db_result"): context["db_result"] = state["db_result"]

    return {**state, "final_response": json.dumps(context)}