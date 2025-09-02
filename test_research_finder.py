import pytest
from unittest.mock import Mock, patch
from research_finder import research_finder, TOOL_SPEC


def test_tool_spec():
    """Test that TOOL_SPEC has required fields."""
    assert TOOL_SPEC["name"] == "research_finder"
    assert "description" in TOOL_SPEC
    assert "inputSchema" in TOOL_SPEC
    assert "topic" in TOOL_SPEC["inputSchema"]["json"]["properties"]


@patch('requests.get')
def test_research_finder_success(mock_get):
    """Test successful research_finder execution."""
    # Mock OpenAlex response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.url = "https://api.openalex.org/works?search=test"
    mock_response.json.return_value = {
        "results": [{
            "title": "Test Paper",
            "authorships": [{"author": {"display_name": "Test Author"}}],
            "publication_year": 2020,
            "host_venue": {"display_name": "Test Journal"},
            "doi": "10.1234/test",
            "abstract_inverted_index": {"test": [0], "abstract": [1]},
            "relevance_score": 0.9,
            "cited_by_count": 10,
            "type": "journal-article"
        }]
    }
    mock_get.return_value = mock_response
    
    tool_use = {
        "toolUseId": "test-123",
        "input": {"topic": "test topic"}
    }
    
    result = research_finder(tool_use)
    
    assert result["toolUseId"] == "test-123"
    assert result["status"] == "success"
    assert "Test Paper" in result["content"][0]["text"]


@patch('requests.get')
def test_research_finder_api_error(mock_get):
    """Test research_finder handles API errors gracefully."""
    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.text = "Forbidden"
    mock_get.return_value = mock_response
    
    tool_use = {
        "toolUseId": "test-456",
        "input": {"topic": "test topic"}
    }
    
    result = research_finder(tool_use)
    
    assert result["toolUseId"] == "test-456"
    assert result["status"] == "success"
    assert "No research papers found" in result["content"][0]["text"]


def test_research_finder_required_params():
    """Test research_finder with minimal required parameters."""
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"results": []}
        
        tool_use = {
            "toolUseId": "test-789",
            "input": {"topic": "minimal test"}
        }
        
        result = research_finder(tool_use)
        assert result["toolUseId"] == "test-789"
        assert result["status"] == "success"