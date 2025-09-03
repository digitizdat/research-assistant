"""Tests for research_finder configuration options."""
import pytest
from unittest.mock import Mock, patch
from research_finder import research_finder


class TestResearchFinderConfiguration:
    """Test configuration options for enabling/disabling research sources."""

    @patch("requests.get")
    def test_openalex_only(self, mock_get):
        """Test with only OpenAlex enabled."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{
                "title": "OpenAlex Paper",
                "authorships": [{"author": {"display_name": "Test Author"}}],
                "publication_year": 2023,
                "host_venue": {"display_name": "Test Journal"},
                "doi": "10.1234/test",
                "abstract_inverted_index": {"test": [0]},
                "relevance_score": 0.9,
                "cited_by_count": 10,
                "type": "journal-article"
            }]
        }
        mock_get.return_value = mock_response

        tool_use = {
            "toolUseId": "test-openalex-only",
            "input": {
                "topic": "test",
                "enable_openalex": True,
                "enable_orkg": False
            }
        }

        result = research_finder(tool_use)

        assert result["status"] == "success"
        content = result["content"][0]["text"]
        assert "OpenAlex Paper" in content
        assert "OpenAlex for bibliographic data" in content
        # Should only call OpenAlex API once
        assert mock_get.call_count == 1

    @patch("requests.get")
    def test_orkg_only(self, mock_get):
        """Test with only ORKG enabled."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "payload": {
                "items": [{
                    "title": "ORKG Paper",
                    "authors": ["ORKG Author"],
                    "year": 2023,
                    "journals": ["ORKG Journal"],
                    "doi": "10.5678/orkg",
                    "abstract": "ORKG test paper",
                    "citation_count": 15,
                    "document_type": "journal"
                }]
            }
        }
        mock_get.return_value = mock_response

        tool_use = {
            "toolUseId": "test-orkg-only",
            "input": {
                "topic": "test",
                "enable_openalex": False,
                "enable_orkg": True
            }
        }

        result = research_finder(tool_use)

        assert result["status"] == "success"
        content = result["content"][0]["text"]
        assert "ORKG Paper" in content
        assert "ORKG Ask for semantic search" in content
        # Should only call ORKG API (with retries)
        assert mock_get.call_count >= 1

    def test_both_disabled(self):
        """Test with both sources disabled."""
        tool_use = {
            "toolUseId": "test-both-disabled",
            "input": {
                "topic": "test",
                "enable_openalex": False,
                "enable_orkg": False
            }
        }

        result = research_finder(tool_use)

        assert result["status"] == "success"
        content = result["content"][0]["text"]
        assert "No research papers found" in content
        assert "No research sources were enabled" in content

    @patch("requests.get")
    def test_default_configuration(self, mock_get):
        """Test default configuration (both enabled)."""
        # Mock both APIs
        def side_effect(url, **kwargs):
            mock_response = Mock()
            mock_response.status_code = 200
            if "openalex" in url:
                mock_response.json.return_value = {"results": []}
            else:  # ORKG
                mock_response.json.return_value = {"payload": {"items": []}}
            return mock_response

        mock_get.side_effect = side_effect

        tool_use = {
            "toolUseId": "test-default",
            "input": {"topic": "test"}  # No explicit enable flags
        }

        result = research_finder(tool_use)

        assert result["status"] == "success"
        content = result["content"][0]["text"]
        assert "OpenAlex for bibliographic data and ORKG Ask" in content

    @patch("requests.get")
    def test_openalex_fails_orkg_succeeds(self, mock_get):
        """Test fallback when OpenAlex fails but ORKG succeeds."""
        def side_effect(url, **kwargs):
            mock_response = Mock()
            if "openalex" in url:
                mock_response.status_code = 500
                return mock_response
            else:  # ORKG
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "payload": {
                        "items": [{
                            "title": "ORKG Fallback Paper",
                            "authors": ["Fallback Author"],
                            "year": 2023,
                            "journals": ["Fallback Journal"],
                            "doi": "10.9999/fallback",
                            "abstract": "Fallback paper from ORKG",
                            "citation_count": 5,
                            "document_type": "journal"
                        }]
                    }
                }
                return mock_response

        mock_get.side_effect = side_effect

        tool_use = {
            "toolUseId": "test-fallback",
            "input": {
                "topic": "test",
                "enable_openalex": True,
                "enable_orkg": True
            }
        }

        result = research_finder(tool_use)

        assert result["status"] == "success"
        content = result["content"][0]["text"]
        assert "ORKG Fallback Paper" in content
        assert "Found 1 relevant research papers" in content

    @pytest.mark.parametrize("enable_openalex,enable_orkg,expected_sources", [
        (True, True, 2),
        (True, False, 1),
        (False, True, 1),
        (False, False, 0)
    ])
    def test_source_counting(self, enable_openalex, enable_orkg, expected_sources):
        """Test that the correct number of sources are queried."""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"results": [], "payload": {"items": []}}
            mock_get.return_value = mock_response

            tool_use = {
                "toolUseId": f"test-sources-{expected_sources}",
                "input": {
                    "topic": "test",
                    "enable_openalex": enable_openalex,
                    "enable_orkg": enable_orkg
                }
            }

            result = research_finder(tool_use)

            assert result["status"] == "success"
            if expected_sources == 0:
                assert mock_get.call_count == 0
            else:
                # ORKG may retry, so check minimum calls
                assert mock_get.call_count >= expected_sources