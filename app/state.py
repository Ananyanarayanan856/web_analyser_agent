from typing import TypedDict, Optional, Any

class AgentState(TypedDict):
    user_input: str
    intent: Optional[str]          # "analyze", "database", "both"
    analysis_types: Optional[list[str]]
    url: Optional[str]
    seo_result: Optional[dict]
    accessibility_result: Optional[dict]
    content_result: Optional[dict]
    db_query: Optional[str]        # JSON string for DB tool
    db_result: Optional[dict]
    browser: Any                   # Global Playwright browser session
    final_response: Optional[str]
    error: Optional[str]
    conversation_history: list