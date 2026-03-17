import re

def website_analyzer_node(state):
    user_input = state.get("user_input", "")

    # Simple regex for URL detection
    url_pattern = r"(https?://[^\s]+|www\.[^\s]+)"
    match = re.search(url_pattern, user_input)

    if match:
        state["url"] = match.group(0)
    else:
        state["url"] = None

    return state