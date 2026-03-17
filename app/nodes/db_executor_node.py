from app.state import AgentState
from app.tools.database_tool import execute_db_query

def db_executor_node(state: AgentState) -> AgentState:
    query = state.get("db_query")
    if not query:
        return {**state, "db_result": {"error": "No query to execute"}}
    result = execute_db_query(query)
    return {**state, "db_result": result}