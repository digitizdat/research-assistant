"""Tests for CORE tool."""
import pytest
from unittest.mock import Mock, patch
from core_tool import core_search, TOOL_SPEC


class TestCORETool:
    """Test the standalone CORE tool."""

    def test_core_tool_spec(self):
        """Test CORE tool specification."""
        assert TOOL_SPEC["name"] == "core_search"
        assert "CORE" in TOOL_SPEC["description"]
        assert "topic" in TOOL_SPEC["inputSchema"]["json"]["properties"]

    @patch("requests.get")
    def test_core_search_success(self, mock_get):
        """Test successful CORE search."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{
                "title": "Test CORE Paper",
                "authors": [{"name": "CORE Author"}],
                "publishedDate": "2023-01-01",
                "publisher": "CORE Publisher",
                "doi": "10.1234/core",
                "abstract": "Test CORE abstract",
                "citationCount": 20
            }]
        }
        mock_get.return_value = mock_response

        tool_use = {
            "toolUseId": "test-core",
            "input": {"topic": "test", "max_results": 5}
        }

        result = core_search(tool_use)

        assert result["status"] == "success"
        content = result["content"][0]["text"]
        assert "Test CORE Paper" in content
        assert "CORE Author" in content
        assert "Citations: 20" in content

    @patch("requests.get")
    def test_core_search_failure(self, mock_get):
        """Test CORE search failure handling."""
        mock_get.side_effect = Exception("Connection failed")

        tool_use = {
            "toolUseId": "test-core-fail",
            "input": {"topic": "test"}
        }

        result = core_search(tool_use)

        assert result["status"] == "success"
        content = result["content"][0]["text"]
        assert "CORE search failed" in content

    @patch("requests.get")
    def test_core_retry_logic(self, mock_get):
        """Test CORE retry logic on rate limiting."""
        responses = [
            Mock(status_code=429),
            Mock(status_code=429),
            Mock(status_code=200)
        ]
        responses[2].json.return_value = {"results": []}
        mock_get.side_effect = responses

        tool_use = {
            "toolUseId": "test-core-retry",
            "input": {"topic": "test"}
        }

        result = core_search(tool_use)

        assert result["status"] == "success"
        assert mock_get.call_count == 3

    @patch("requests.get")
    def test_core_year_filtering(self, mock_get):
        """Test CORE year filtering."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "title": "Old Paper",
                    "publishedDate": "2010-01-01",
                    "authors": [{"name": "Old Author"}],
                    "publisher": "Old Publisher"
                },
                {
                    "title": "Recent Paper", 
                    "publishedDate": "2023-01-01",
                    "authors": [{"name": "New Author"}],
                    "publisher": "New Publisher"
                }
            ]
        }
        mock_get.return_value = mock_response

        tool_use = {
            "toolUseId": "test-core-filter",
            "input": {"topic": "test", "min_year": 2020}
        }

        result = core_search(tool_use)

        content = result["content"][0]["text"]
        assert "Recent Paper" in content
        assert "Old Paper" not in content