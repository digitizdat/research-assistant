"""Tests for query router tool."""

from unittest.mock import patch

from query_router import TOOL_SPEC, query_router


def test_tool_spec():
    """Test tool specification is properly defined."""
    assert TOOL_SPEC["name"] == "query_router"
    assert "query" in TOOL_SPEC["inputSchema"]["json"]["properties"]
    assert "query" in TOOL_SPEC["inputSchema"]["json"]["required"]


@patch("query_router.config_manager_tool")
def test_config_commands_routed_to_config_tool(mock_config_tool):
    """Test configuration commands are routed to config tool."""
    mock_config_tool.return_value = {
        "toolUseId": "test",
        "status": "success",
        "content": [{"text": "Config updated"}],
    }

    config_queries = [
        "enable orkg tool",
        "disable openalex",
        "set timeout to 60",
        "set core retries to 5",
        "show config",
        "configure settings",
        "config update",
    ]

    for query in config_queries:
        tool_use = {"toolUseId": "test", "input": {"query": query}}
        result = query_router(tool_use)

        mock_config_tool.assert_called()
        assert result["status"] == "success"


@patch("query_router.research_finder")
def test_research_queries_routed_to_research_tool(mock_research_tool):
    """Test research queries are routed to research finder."""
    mock_research_tool.return_value = {
        "toolUseId": "test",
        "status": "success",
        "content": [{"text": "Research results"}],
    }

    research_queries = [
        "machine learning algorithms",
        "climate change impacts",
        "quantum computing research",
        "artificial intelligence ethics",
        "renewable energy technologies",
    ]

    for query in research_queries:
        tool_use = {"toolUseId": "test", "input": {"query": query}}
        result = query_router(tool_use)

        mock_research_tool.assert_called()
        assert result["status"] == "success"


@patch("query_router.config_manager_tool")
@patch("query_router.research_finder")
def test_tool_use_id_propagation(mock_research_tool, mock_config_tool):
    """Test tool use IDs are properly propagated."""
    mock_config_tool.return_value = {
        "toolUseId": "test-config",
        "status": "success",
        "content": [{"text": "Config"}],
    }
    mock_research_tool.return_value = {
        "toolUseId": "test-research",
        "status": "success",
        "content": [{"text": "Research"}],
    }

    # Test config routing
    tool_use = {"toolUseId": "main-123", "input": {"query": "enable orkg"}}
    query_router(tool_use)
    mock_config_tool.assert_called_with(
        {"toolUseId": "main-123", "input": {"command": "enable orkg"}}
    )

    # Test research routing
    tool_use = {"toolUseId": "main-456", "input": {"query": "machine learning"}}
    query_router(tool_use)
    mock_research_tool.assert_called_with(
        {"toolUseId": "main-456", "input": {"topic": "machine learning"}}
    )
