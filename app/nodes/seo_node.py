from app.state import AgentState
from app.tools.seo import seo_analyzer

def seo_node(state: AgentState) -> AgentState:
    types = state.get("analysis_types", [])
    if "seo" not in types:
        return state
        
    url = state.get("url")
    browser = state.get("browser")
    if not url:
        return {**state, "seo_result": {"error": "No URL provided"}}
    if not browser:
        return {**state, "seo_result": {"error": "No browser instance provided"}}
    
    result = seo_analyzer(url, browser=browser)
    return {**state, "seo_result": result}