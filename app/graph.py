# app/graph.py
from langgraph.graph import StateGraph, END
from app.state import AgentState
from app.nodes.intent_router_node import intent_router_node
from app.nodes.seo_node import seo_node
from app.nodes.accessibility_node import accessibility_node
from app.nodes.content_node import content_node
from app.nodes.db_query_generator_node import db_query_generator_node
from app.nodes.db_executor_node import db_executor_node
from app.nodes.response_formatter_node import response_formatter_node

def route_intent(state: AgentState):
    intent = state.get("intent", "analyze_website")
    if intent == "database_query":
        return "db_query_generator"
    elif intent == "both":
        return "seo"  # analyze first, then DB
    else:
        return "seo"

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("intent_router", intent_router_node)
    graph.add_node("seo", seo_node)
    graph.add_node("accessibility", accessibility_node)
    graph.add_node("content", content_node)
    graph.add_node("db_query_generator", db_query_generator_node)
    graph.add_node("db_executor", db_executor_node)
    graph.add_node("response_formatter", response_formatter_node)

    graph.set_entry_point("intent_router")

    graph.add_conditional_edges("intent_router", route_intent, {
        "seo": "seo",
        "db_query_generator": "db_query_generator"
    })

    # Website analysis chain
    graph.add_edge("seo", "accessibility")
    graph.add_edge("accessibility", "content")

    # After content: check if we also need DB (intent == "both")
    def after_content(state: AgentState):
        return "db_query_generator" if state.get("intent") == "both" else "response_formatter"

    graph.add_conditional_edges("content", after_content, {
        "db_query_generator": "db_query_generator",
        "response_formatter": "response_formatter"
    })

    # DB chain
    graph.add_edge("db_query_generator", "db_executor")
    graph.add_edge("db_executor", "response_formatter")
    graph.add_edge("response_formatter", END)

    return graph.compile()

agent = build_graph()