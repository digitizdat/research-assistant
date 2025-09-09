import re
from typing import Any

from strands.types.tools import ToolResult, ToolUse

from config_manager_tool import config_manager_tool
from research_finder import research_finder

TOOL_SPEC = {
    "name": "query_router",
    "description": "Routes user queries to either research finder or configuration management based on query intent",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "User query to route to appropriate tool",
                }
            },
            "required": ["query"],
        }
    },
}


def query_router(tool_use: ToolUse, **kwargs: Any) -> ToolResult:
    """Route user queries to appropriate tool based on intent detection."""
    tool_use_id = tool_use["toolUseId"]
    query = tool_use["input"]["query"]

    # Configuration command patterns
    config_patterns = [
        r"(enable|disable)\s+(?:the\s+)?(\w+)(?:\s+tool)?",
        r"set\s+(?:the\s+)?(\w+)?\s*timeout\s+to\s+(\d+)",
        r"set\s+(?:the\s+)?(\w+)?\s*retries?\s+to\s+(\d+)",
        r"show\s+config",
        r"configure\s+",
        r"config\s+",
        r"settings\s+",
    ]

    query_lower = query.lower().strip()

    # Check if this is a configuration command
    is_config = any(re.search(pattern, query_lower) for pattern in config_patterns)

    if is_config:
        # Route to configuration tool
        config_tool_use = {"toolUseId": tool_use_id, "input": {"command": query}}
        return config_manager_tool(config_tool_use)
    else:
        # Route to research finder
        research_tool_use = {"toolUseId": tool_use_id, "input": {"topic": query}}
        return research_finder(research_tool_use)
