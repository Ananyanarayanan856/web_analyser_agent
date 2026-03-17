from app.state import AgentState
from app.tools.accessibility import accessibility_analyzer

def accessibility_node(state: AgentState) -> AgentState:
    types = state.get("analysis_types", [])
    if "accessibility" not in types:
        return state
        
    url = state.get("url")
    browser = state.get("browser")
    if not url:
        return {**state, "accessibility_result": {"error": "No URL provided"}}
    if not browser:
        return {**state, "accessibility_result": {"error": "No browser instance provided"}}
        
    result = accessibility_analyzer(url, browser=browser)
    return {**state, "accessibility_result": result}