from unittest.mock import patch

from research_finder import TOOL_SPEC, research_finder


def test_tool_spec():
    """Test that TOOL_SPEC has required fields."""
    assert TOOL_SPEC["name"] == "research_finder"
    assert "description" in TOOL_SPEC
    assert "inputSchema" in TOOL_SPEC
    assert "topic" in TOOL_SPEC["inputSchema"]["json"]["properties"]


@patch("research_finder.openalex_search")
@patch("research_finder.config")
def test_research_finder_success(mock_config, mock_openalex):
    """Test successful research_finder execution."""
    # Mock config
    mock_config.get_defaults.return_value = {"max_results": 10, "min_year": 2004}
    mock_config.get_behavior_config.return_value = {"max_workers": 3}
    mock_config.is_source_enabled.side_effect = lambda x: x == "openalex"
    mock_config.get_source_config.return_value = {"timeout": 40}

    # Mock OpenAlex search
    mock_openalex.return_value = {
        "toolUseId": "test-123-openalex",
        "status": "success",
        "content": [
            {
                "text": "**1. Test Paper**\n👥 Authors: Test Author\n📅 Year: 2020\n📖 Published in: Test Journal\n📈 Citations: 10\n📝 Summary: Test abstract\n🔗 DOI: 10.1234/test"
            }
        ],
    }

    tool_use = {"toolUseId": "test-123", "input": {"topic": "test topic"}}

    result = research_finder(tool_use)

    assert result["toolUseId"] == "test-123"
    assert result["status"] == "success"
    assert "Test Paper" in result["content"][0]["text"]


@patch("research_finder.openalex_search")
@patch("research_finder.config")
def test_research_finder_api_error(mock_config, mock_openalex):
    """Test research_finder handles API errors gracefully."""
    # Mock config
    mock_config.get_defaults.return_value = {"max_results": 10, "min_year": 2004}
    mock_config.get_behavior_config.return_value = {"max_workers": 3}
    mock_config.is_source_enabled.side_effect = lambda x: x == "openalex"
    mock_config.get_source_config.return_value = {"timeout": 40}

    # Mock OpenAlex search failure
    mock_openalex.side_effect = Exception("API Error")

    tool_use = {"toolUseId": "test-456", "input": {"topic": "test topic"}}

    result = research_finder(tool_use)

    assert result["toolUseId"] == "test-456"
    assert result["status"] == "success"
    assert "No research papers found" in result["content"][0]["text"]


@patch("research_finder.openalex_search")
@patch("research_finder.config")
def test_research_finder_required_params(mock_config, mock_openalex):
    """Test research_finder with minimal required parameters."""
    mock_config.get_defaults.return_value = {"max_results": 10, "min_year": 2004}
    mock_config.get_behavior_config.return_value = {"max_workers": 3}
    mock_config.is_source_enabled.side_effect = lambda x: x == "openalex"
    mock_config.get_source_config.return_value = {"timeout": 40}
    mock_openalex.return_value = {
        "toolUseId": "test-789-openalex",
        "status": "success",
        "content": [{"text": "No papers found"}],
    }

    tool_use = {"toolUseId": "test-789", "input": {"topic": "minimal test"}}

    result = research_finder(tool_use)
    assert result["toolUseId"] == "test-789"
    assert result["status"] == "success"
