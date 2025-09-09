import re
from typing import Any

from strands.types.tools import ToolResult, ToolUse

from config_manager import ConfigManager

TOOL_SPEC = {
    "name": "config_manager_tool",
    "description": "Manage research assistant configuration settings through natural language commands",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Natural language command to modify configuration (e.g., 'enable ORKG tool', 'set timeout to 60', 'show config')",
                }
            },
            "required": ["command"],
        }
    },
}


def config_manager_tool(tool_use: ToolUse, **kwargs: Any) -> ToolResult:
    """Execute a configuration management command through natural language."""
    tool_use_id = tool_use["toolUseId"]
    command = tool_use["input"]["command"]

    try:
        config_manager = ConfigManager()
        config = config_manager.load_config()

        command_lower = command.lower().strip()

        # Enable/disable patterns
        if match := re.search(
            r"(enable|disable)\s+(?:the\s+)?(\w+)(?:\s+tool)?", command_lower
        ):
            action, tool = match.groups()
            result = _toggle_tool(config, config_manager, tool, action == "enable")

        # Set timeout patterns
        elif match := re.search(
            r"set\s+(?:the\s+)?(\w+)?\s*timeout\s+to\s+(\d+)", command_lower
        ):
            tool, timeout = match.groups()
            result = _set_timeout(config, config_manager, tool, int(timeout))

        # Set retry patterns
        elif match := re.search(
            r"set\s+(?:the\s+)?(\w+)?\s*retries?\s+to\s+(\d+)", command_lower
        ):
            tool, retries = match.groups()
            result = _set_retries(config, config_manager, tool, int(retries))

        # Show config
        elif "show" in command_lower and "config" in command_lower:
            result = _show_config(config)

        else:
            result = f"Unknown command: {command}"

        return {
            "toolUseId": tool_use_id,
            "status": "success",
            "content": [{"text": result}],
        }

    except Exception as e:
        return {
            "toolUseId": tool_use_id,
            "status": "error",
            "content": [{"text": f"Error processing command: {str(e)}"}],
        }


def _toggle_tool(config, config_manager, tool, enable):
    """Enable or disable a tool."""
    tool_map = {"openalex": "openalex", "orkg": "orkg", "core": "core"}

    if tool not in tool_map:
        return f"Unknown tool: {tool}. Available: {', '.join(tool_map.keys())}"

    tool_key = tool_map[tool]
    if "sources" not in config:
        config["sources"] = {}
    if tool_key not in config["sources"]:
        config["sources"][tool_key] = {}

    config["sources"][tool_key]["enabled"] = enable
    config_manager.save_config(config)

    status = "enabled" if enable else "disabled"
    return f"{tool.upper()} tool {status}"


def _set_timeout(config, config_manager, tool, timeout):
    """Set timeout for a tool or globally."""
    if not tool:
        # Set global timeout
        if "sources" in config:
            for tool_config in config["sources"].values():
                if isinstance(tool_config, dict):
                    tool_config["timeout"] = timeout
        config_manager.save_config(config)
        return f"Global timeout set to {timeout} seconds"

    tool_map = {"openalex": "openalex", "orkg": "orkg", "core": "core"}
    if tool not in tool_map:
        return f"Unknown tool: {tool}"

    tool_key = tool_map[tool]
    if "sources" not in config:
        config["sources"] = {}
    if tool_key not in config["sources"]:
        config["sources"][tool_key] = {}

    config["sources"][tool_key]["timeout"] = timeout
    config_manager.save_config(config)
    return f"{tool.upper()} timeout set to {timeout} seconds"


def _set_retries(config, config_manager, tool, retries):
    """Set retry count for a tool or globally."""
    if not tool:
        # Set global retries
        if "sources" in config:
            for tool_config in config["sources"].values():
                if isinstance(tool_config, dict):
                    tool_config["max_retries"] = retries
        config_manager.save_config(config)
        return f"Global retries set to {retries}"

    tool_map = {"openalex": "openalex", "orkg": "orkg", "core": "core"}
    if tool not in tool_map:
        return f"Unknown tool: {tool}"

    tool_key = tool_map[tool]
    if "sources" not in config:
        config["sources"] = {}
    if tool_key not in config["sources"]:
        config["sources"][tool_key] = {}

    config["sources"][tool_key]["max_retries"] = retries
    config_manager.save_config(config)
    return f"{tool.upper()} retries set to {retries}"


def _show_config(config):
    """Show current configuration."""
    lines = ["Current Configuration:"]

    sources = config.get("sources", {})
    for tool in ["openalex", "orkg", "core"]:
        if tool in sources:
            cfg = sources[tool]
            enabled = cfg.get("enabled", True)
            timeout = cfg.get("timeout", 30)
            retries = cfg.get("max_retries", 3)
            lines.append(
                f"  {tool.upper()}: {'enabled' if enabled else 'disabled'}, timeout={timeout}s, retries={retries}"
            )

    return "\n".join(lines)
