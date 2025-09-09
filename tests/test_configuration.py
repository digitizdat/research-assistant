"""Tests for research_finder configuration options."""

from unittest.mock import patch

import pytest

from research_finder import research_finder


class TestResearchFinderConfiguration:
    """Test configuration options for enabling/disabling research sources."""

    @patch("research_finder.openalex_search")
    @patch("research_finder.config")
    def test_openalex_only(self, mock_config, mock_openalex):
        """Test with only OpenAlex enabled."""
        mock_config.get_defaults.return_value = {"max_results": 10, "min_year": 2004}
        mock_config.get_behavior_config.return_value = {"max_workers": 3}
        mock_config.is_source_enabled.side_effect = lambda x: x == "openalex"
        mock_config.get_source_config.return_value = {"timeout": 40}

        mock_openalex.return_value = {
            "toolUseId": "test-openalex-only-openalex",
            "status": "success",
            "content": [
                {
                    "text": "**1. OpenAlex Paper**\n👥 Authors: Test Author\n📅 Year: 2023\n📖 Published in: Test Journal\n📈 Citations: 10\n📝 Summary: Test abstract\n🔗 DOI: 10.1234/test"
                }
            ],
        }

        tool_use = {
            "toolUseId": "test-openalex-only",
            "input": {
                "topic": "test",
                "enable_openalex": True,
                "enable_orkg": False,
                "enable_core": False,
            },
        }

        result = research_finder(tool_use)

        assert result["status"] == "success"
        content = result["content"][0]["text"]
        assert "OpenAlex Paper" in content
        assert "OpenAlex for bibliographic data" in content

    @patch("research_finder.orkg_search")
    @patch("research_finder.config")
    def test_orkg_only(self, mock_config, mock_orkg):
        """Test with only ORKG enabled."""
        mock_config.get_defaults.return_value = {"max_results": 10, "min_year": 2004}
        mock_config.get_behavior_config.return_value = {"max_workers": 3}
        mock_config.is_source_enabled.side_effect = lambda x: x == "orkg"
        mock_config.get_source_config.return_value = {"timeout": 60}

        mock_orkg.return_value = {
            "toolUseId": "test-orkg-only-orkg",
            "status": "success",
            "content": [
                {
                    "text": "**1. ORKG Paper**\n👥 Authors: ORKG Author\n📅 Year: 2023\n📖 Published in: ORKG Journal\n📈 Citations: 15\n📝 Summary: ORKG test paper\n🔗 DOI: 10.5678/orkg"
                }
            ],
        }

        tool_use = {
            "toolUseId": "test-orkg-only",
            "input": {
                "topic": "test",
                "enable_openalex": False,
                "enable_orkg": True,
                "enable_core": False,
            },
        }

        result = research_finder(tool_use)

        assert result["status"] == "success"
        content = result["content"][0]["text"]
        assert "ORKG Paper" in content
        assert "ORKG Ask for semantic search" in content

    @patch("research_finder.config")
    def test_both_disabled(self, mock_config):
        """Test with all sources disabled."""
        mock_config.get_defaults.return_value = {"max_results": 10, "min_year": 2004}
        mock_config.get_behavior_config.return_value = {"max_workers": 3}
        mock_config.is_source_enabled.return_value = False

        tool_use = {
            "toolUseId": "test-both-disabled",
            "input": {
                "topic": "test",
                "enable_openalex": False,
                "enable_orkg": False,
                "enable_core": False,
            },
        }

        result = research_finder(tool_use)

        assert result["status"] == "success"
        content = result["content"][0]["text"]
        assert "No research papers found" in content
        assert "No research sources were enabled" in content

    @patch("research_finder.orkg_search")
    @patch("research_finder.openalex_search")
    @patch("research_finder.config")
    def test_default_configuration(self, mock_config, mock_openalex, mock_orkg):
        """Test default configuration (multiple sources enabled)."""
        mock_config.get_defaults.return_value = {"max_results": 10, "min_year": 2004}
        mock_config.get_behavior_config.return_value = {"max_workers": 3}
        mock_config.is_source_enabled.return_value = True
        mock_config.get_source_config.return_value = {"timeout": 40}

        mock_openalex.return_value = {
            "toolUseId": "test-default-openalex",
            "status": "success",
            "content": [{"text": "No papers found"}],
        }
        mock_orkg.return_value = {
            "toolUseId": "test-default-orkg",
            "status": "success",
            "content": [{"text": "No papers found"}],
        }

        tool_use = {
            "toolUseId": "test-default",
            "input": {"topic": "test"},
        }

        result = research_finder(tool_use)

        assert result["status"] == "success"
        content = result["content"][0]["text"]
        assert (
            "OpenAlex for bibliographic data, ORKG Ask for semantic search, CORE for open access papers"
            in content
        )

    @pytest.mark.parametrize(
        "enable_openalex,enable_orkg,enable_core,expected_sources",
        [
            (True, True, True, 3),
            (True, False, False, 1),
            (False, True, False, 1),
            (False, False, False, 0),
        ],
    )
    @patch("research_finder.core_search")
    @patch("research_finder.orkg_search")
    @patch("research_finder.openalex_search")
    @patch("research_finder.config")
    def test_source_counting(
        self,
        mock_config,
        mock_openalex,
        mock_orkg,
        mock_core,
        enable_openalex,
        enable_orkg,
        enable_core,
        expected_sources,
    ):
        """Test that the correct number of sources are queried."""
        mock_config.get_defaults.return_value = {"max_results": 10, "min_year": 2004}
        mock_config.get_behavior_config.return_value = {"max_workers": 3}
        mock_config.is_source_enabled.return_value = False
        mock_config.get_source_config.return_value = {"timeout": 40}

        empty_result = {"status": "success", "content": [{"text": "No papers found"}]}
        mock_openalex.return_value = empty_result
        mock_orkg.return_value = empty_result
        mock_core.return_value = empty_result

        tool_use = {
            "toolUseId": f"test-sources-{expected_sources}",
            "input": {
                "topic": "test",
                "enable_openalex": enable_openalex,
                "enable_orkg": enable_orkg,
                "enable_core": enable_core,
            },
        }

        result = research_finder(tool_use)

        assert result["status"] == "success"

        # Check that correct number of tools were called
        call_count = 0
        if enable_openalex:
            mock_openalex.assert_called_once()
            call_count += 1
        if enable_orkg:
            mock_orkg.assert_called_once()
            call_count += 1
        if enable_core:
            mock_core.assert_called_once()
            call_count += 1

        assert call_count == expected_sources
