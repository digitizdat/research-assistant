# Tool Creation Guidelines

When creating new tools, use this system prompt approach:

## TOOL NAMING CONVENTION:
- Tool name (function name) MUST match file name without extension
- Example: For file "tool_name.py", use tool name "tool_name"

## TOOL CREATION vs. TOOL USAGE:
- Distinguish between requests to CREATE vs USE existing tools
- Check if appropriate tool exists before creating new one
- Only create when explicitly requested with "create", "make a tool", etc.

## TOOL CREATION PROCESS:
- Name file "tool_name.py" 
- Function name SAME as file name (without extension)
- "name" parameter in TOOL_SPEC MUST match file name
- Include detailed docstrings
- Announce "TOOL_CREATED: <filename>" after creation

## TOOL STRUCTURE:
```python
from typing import Any
from strands.types.tools import ToolUse, ToolResult

TOOL_SPEC = {
    "name": "tool_name",  # Must match function name
    "description": "What the tool does",
    "inputSchema": {  # Exact capitalization required
        "json": {
            "type": "object",
            "properties": {
                "param_name": {
                    "type": "string",
                    "description": "Parameter description"
                }
            },
            "required": ["param_name"]
        }
    }
}

def tool_name(tool_use: ToolUse, **kwargs: Any) -> ToolResult:
    tool_use_id = tool_use["toolUseId"]
    param_value = tool_use["input"]["param_name"]
    
    # Process inputs
    result = param_value  # Replace with actual processing
    
    return {
        "toolUseId": tool_use_id,
        "status": "success",
        "content": [{"text": f"Result: {result}"}]
    }
```