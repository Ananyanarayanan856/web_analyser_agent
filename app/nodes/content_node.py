from app.state import AgentState
from app.tools.content import content_analyzer

def content_node(state: AgentState) -> AgentState:
    types = state.get("analysis_types", [])
    if "content" not in types:
        return state
        
    url = state.get("url")
    browser = state.get("browser")
    if not url:
        return {**state, "content_result": {"error": "No URL provided"}}
    if not browser:
        return {**state, "content_result": {"error": "No browser instance provided"}}
        
    result = content_analyzer(url, browser=browser)
    return {**state, "content_result": result}