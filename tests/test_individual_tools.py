"""Tests for individual OpenAlex and ORKG tools."""

from unittest.mock import Mock, patch

from openalex_tool import TOOL_SPEC as OPENALEX_SPEC
from openalex_tool import openalex_search
from orkg_tool import TOOL_SPEC as ORKG_SPEC
from orkg_tool import orkg_search


class TestOpenAlexTool:
    """Test the standalone OpenAlex tool."""

    def test_openalex_tool_spec(self):
        """Test OpenAlex tool specification."""
        assert OPENALEX_SPEC["name"] == "openalex_search"
        assert "OpenAlex" in OPENALEX_SPEC["description"]
        assert "topic" in OPENALEX_SPEC["inputSchema"]["json"]["properties"]

    @patch("requests.get")
    def test_openalex_search_success(self, mock_get):
        """Test successful OpenAlex search."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "title": "Test OpenAlex Paper",
                    "authorships": [{"author": {"display_name": "Test Author"}}],
                    "publication_year": 2023,
                    "host_venue": {"display_name": "Test Journal"},
                    "doi": "10.1234/test",
                    "abstract_inverted_index": {"test": [0], "paper": [1]},
                    "relevance_score": 0.9,
                    "cited_by_count": 15,
                    "type": "journal-article",
                }
            ]
        }
        mock_get.return_value = mock_response

        tool_use = {
            "toolUseId": "test-openalex",
            "input": {"topic": "test", "max_results": 5},
        }

        result = openalex_search(tool_use)

        assert result["status"] == "success"
        content = result["content"][0]["text"]
        assert "Test OpenAlex Paper" in content
        assert "Test Author" in content
        assert "Citations: 15" in content

    @patch("requests.get")
    def test_openalex_search_failure(self, mock_get):
        """Test OpenAlex search failure handling."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        mock_get.return_value = mock_response

        tool_use = {"toolUseId": "test-openalex-fail", "input": {"topic": "test"}}

        result = openalex_search(tool_use)

        assert result["status"] == "success"
        content = result["content"][0]["text"]
        assert "OpenAlex search failed" in content


class TestORKGTool:
    """Test the standalone ORKG tool."""

    def test_orkg_tool_spec(self):
        """Test ORKG tool specification."""
        assert ORKG_SPEC["name"] == "orkg_search"
        assert "ORKG" in ORKG_SPEC["description"]
        assert "topic" in ORKG_SPEC["inputSchema"]["json"]["properties"]

    @patch("requests.get")
    def test_orkg_search_success(self, mock_get):
        """Test successful ORKG search."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "payload": {
                "items": [
                    {
                        "title": "Test ORKG Paper",
                        "authors": ["ORKG Author"],
                        "year": 2023,
                        "journals": ["ORKG Journal"],
                        "doi": "10.5678/orkg",
                        "abstract": "Test ORKG abstract",
                        "citation_count": 10,
                        "document_type": "journal",
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        tool_use = {
            "toolUseId": "test-orkg",
            "input": {"topic": "test", "max_results": 5},
        }

        result = orkg_search(tool_use)

        assert result["status"] == "success"
        content = result["content"][0]["text"]
        assert "Test ORKG Paper" in content
        assert "ORKG Author" in content
        assert "Citations: 10" in content

    @patch("requests.get")
    def test_orkg_search_failure(self, mock_get):
        """Test ORKG search failure handling."""
        mock_get.side_effect = Exception("Connection failed")

        tool_use = {"toolUseId": "test-orkg-fail", "input": {"topic": "test"}}

        result = orkg_search(tool_use)

        assert result["status"] == "success"
        content = result["content"][0]["text"]
        assert "ORKG search failed" in content

    @patch("requests.get")
    def test_orkg_retry_logic(self, mock_get):
        """Test ORKG retry logic on rate limiting."""
        # First two calls return 429, third succeeds
        responses = [
            Mock(status_code=429),
            Mock(status_code=429),
            Mock(status_code=200),
        ]
        responses[2].json.return_value = {"payload": {"items": []}}
        mock_get.side_effect = responses

        tool_use = {"toolUseId": "test-orkg-retry", "input": {"topic": "test"}}

        result = orkg_search(tool_use)

        assert result["status"] == "success"
        assert mock_get.call_count == 3  # Should retry twice then succeed


class TestToolIntegration:
    """Test integration between tools."""

    def test_tools_work_independently(self):
        """Test that tools work independently."""
        with patch("requests.get") as mock_get:
            # Mock response for both tools
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"results": [], "payload": {"items": []}}
            mock_get.return_value = mock_response

            # Test OpenAlex tool
            openalex_tool_use = {
                "toolUseId": "test-openalex-independent",
                "input": {"topic": "test"},
            }
            openalex_result = openalex_search(openalex_tool_use)
            assert openalex_result["status"] == "success"

            # Reset mock for ORKG test
            mock_get.reset_mock()

            # Test ORKG tool
            orkg_tool_use = {
                "toolUseId": "test-orkg-independent",
                "input": {"topic": "test"},
            }
            orkg_result = orkg_search(orkg_tool_use)
            assert orkg_result["status"] == "success"

            # Verify ORKG was called
            assert mock_get.called
