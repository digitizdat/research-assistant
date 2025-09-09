"""Configuration management tool for research assistant."""

import re

from config_manager import ConfigManager


class ConfigTool:
    """Tool for managing research assistant configuration via natural language."""

    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()

    def process_command(self, command: str) -> str:
        """Process a natural language configuration command."""
        command = command.lower().strip()

        # Enable/disable patterns
        if match := re.search(
            r"(enable|disable)\s+(?:the\s+)?(\w+)(?:\s+tool)?", command
        ):
            action, tool = match.groups()
            return self._toggle_tool(tool, action == "enable")

        # Set timeout patterns
        if match := re.search(
            r"set\s+(?:the\s+)?(\w+)?\s*timeout\s+to\s+(\d+)", command
        ):
            tool, timeout = match.groups()
            return self._set_timeout(tool, int(timeout))

        # Set retry patterns
        if match := re.search(
            r"set\s+(?:the\s+)?(\w+)?\s*retries?\s+to\s+(\d+)", command
        ):
            tool, retries = match.groups()
            return self._set_retries(tool, int(retries))

        # Show config
        if "show" in command and "config" in command:
            return self._show_config()

        return f"Unknown command: {command}"

    def _toggle_tool(self, tool: str, enable: bool) -> str:
        """Enable or disable a tool."""
        tool_map = {"openalex": "openalex", "orkg": "orkg", "core": "core"}

        if tool not in tool_map:
            return f"Unknown tool: {tool}. Available: {', '.join(tool_map.keys())}"

        tool_key = tool_map[tool]
        if "sources" not in self.config:
            self.config["sources"] = {}
        if tool_key not in self.config["sources"]:
            self.config["sources"][tool_key] = {}

        self.config["sources"][tool_key]["enabled"] = enable
        self._save_config()

        status = "enabled" if enable else "disabled"
        return f"{tool.upper()} tool {status}"

    def _set_timeout(self, tool: str, timeout: int) -> str:
        """Set timeout for a tool or globally."""
        if not tool:
            # Set global timeout
            if "sources" in self.config:
                for tool_config in self.config["sources"].values():
                    if isinstance(tool_config, dict):
                        tool_config["timeout"] = timeout
            self._save_config()
            return f"Global timeout set to {timeout} seconds"

        tool_map = {"openalex": "openalex", "orkg": "orkg", "core": "core"}
        if tool not in tool_map:
            return f"Unknown tool: {tool}"

        tool_key = tool_map[tool]
        if "sources" not in self.config:
            self.config["sources"] = {}
        if tool_key not in self.config["sources"]:
            self.config["sources"][tool_key] = {}

        self.config["sources"][tool_key]["timeout"] = timeout
        self._save_config()
        return f"{tool.upper()} timeout set to {timeout} seconds"

    def _set_retries(self, tool: str, retries: int) -> str:
        """Set retry count for a tool or globally."""
        if not tool:
            # Set global retries
            if "sources" in self.config:
                for tool_config in self.config["sources"].values():
                    if isinstance(tool_config, dict):
                        tool_config["max_retries"] = retries
            self._save_config()
            return f"Global retries set to {retries}"

        tool_map = {"openalex": "openalex", "orkg": "orkg", "core": "core"}
        if tool not in tool_map:
            return f"Unknown tool: {tool}"

        tool_key = tool_map[tool]
        if "sources" not in self.config:
            self.config["sources"] = {}
        if tool_key not in self.config["sources"]:
            self.config["sources"][tool_key] = {}

        self.config["sources"][tool_key]["max_retries"] = retries
        self._save_config()
        return f"{tool.upper()} retries set to {retries}"

    def _show_config(self) -> str:
        """Show current configuration."""
        lines = ["Current Configuration:"]

        sources = self.config.get("sources", {})
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

    def _save_config(self):
        """Save configuration to file."""
        self.config_manager.save_config(self.config)


# Tool specification for Strands
def get_tool_spec():
    """Get the tool specification for Strands integration."""
    return {
        "name": "config_manager",
        "description": "Manage research assistant configuration settings",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Natural language command to modify configuration (e.g., 'enable ORKG tool', 'set timeout to 60', 'show config')",
                }
            },
            "required": ["command"],
        },
    }


def config_manager(command: str) -> str:
    """Execute a configuration management command."""
    tool = ConfigTool()
    return tool.process_command(command)
