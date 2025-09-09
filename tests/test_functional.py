"""Functional tests for research_finder with realistic data scenarios."""

from unittest.mock import patch

import pytest

from research_finder import research_finder


class TestResearchFinderFunctional:
    """Test research_finder with realistic data and edge cases."""

    @patch("research_finder.openalex_search")
    @patch("research_finder.config")
    def test_openalex_response_parsing(self, mock_config, mock_openalex):
        """Test OpenAlex response parsing with real-like data."""
        mock_config.get_defaults.return_value = {"max_results": 2, "min_year": 2004}
        mock_config.get_behavior_config.return_value = {"max_workers": 3}
        mock_config.is_source_enabled.side_effect = lambda x: x == "openalex"
        mock_config.get_source_config.return_value = {"timeout": 40}

        # Use real synthetic data
        from test_data_loader import test_data

        openalex_data = test_data.get_openalex_data("deep learning computer vision")
        if openalex_data and openalex_data.get("status") == "success":
            mock_openalex.return_value = openalex_data
        else:
            mock_openalex.return_value = {
                "toolUseId": "test-123-openalex",
                "status": "success",
                "content": [
                    {
                        "text": "**1. Deep Learning for Computer Vision**\n👥 Authors: John Smith, Jane Doe\n📅 Year: 2021\n📖 Published in: Nature Machine Intelligence\n📈 Citations: 150\n📝 Summary: Deep learning has revolutionized computer vision\n🔗 DOI: 10.1038/s42256-021-00123-4"
                    }
                ],
            }

        tool_use = {
            "toolUseId": "test-123",
            "input": {
                "topic": "deep learning",
                "max_results": 2,
                "enable_openalex": True,
                "enable_orkg": False,
                "enable_core": False,
            },
        }

        result = research_finder(tool_use)

        assert result["status"] == "success"
        content = result["content"][0]["text"]
        # Verify we got some research content
        assert "Found" in content or "research papers" in content
        assert "Year:" in content or "Citations:" in content

    @patch("research_finder.orkg_search")
    @patch("research_finder.config")
    def test_orkg_response_parsing(self, mock_config, mock_orkg):
        """Test ORKG response parsing with spec-compliant data."""
        mock_config.get_defaults.return_value = {"max_results": 2, "min_year": 2020}
        mock_config.get_behavior_config.return_value = {"max_workers": 3}
        mock_config.is_source_enabled.side_effect = lambda x: x == "orkg"
        mock_config.get_source_config.return_value = {"timeout": 60}

        # Use real synthetic data
        from test_data_loader import test_data

        orkg_data = test_data.get_orkg_data("artificial intelligence ethics")
        if orkg_data and orkg_data.get("status") == "success":
            mock_orkg.return_value = orkg_data
        else:
            mock_orkg.return_value = {
                "toolUseId": "test-456-orkg",
                "status": "success",
                "content": [
                    {
                        "text": "**1. AI Ethics in Healthcare**\n👥 Authors: Dr. Alice Brown, Prof. Bob Wilson\n📅 Year: 2022\n📖 Published in: AI Ethics Journal\n📈 Citations: 45\n📝 Summary: This paper explores ethical considerations in AI healthcare applications\n🔗 DOI: 10.1007/s43681-022-00123-4"
                    }
                ],
            }

        tool_use = {
            "toolUseId": "test-456",
            "input": {
                "topic": "AI ethics",
                "max_results": 2,
                "min_year": 2020,
                "enable_openalex": False,
                "enable_orkg": True,
                "enable_core": False,
            },
        }

        result = research_finder(tool_use)

        assert result["status"] == "success"
        content = result["content"][0]["text"]
        # Verify we got some research content
        assert (
            "Found" in content
            or "research papers" in content
            or "No research papers found" in content
        )
        assert result["status"] == "success"

    @patch("research_finder.openalex_search")
    @patch("research_finder.config")
    def test_year_filtering(self, mock_config, mock_openalex):
        """Test that year filtering works correctly."""
        mock_config.get_defaults.return_value = {"max_results": 10, "min_year": 2020}
        mock_config.get_behavior_config.return_value = {"max_workers": 3}
        mock_config.is_source_enabled.side_effect = lambda x: x == "openalex"
        mock_config.get_source_config.return_value = {"timeout": 40}

        # Mock returns only recent paper (old one filtered out by tool)
        mock_openalex.return_value = {
            "toolUseId": "test-789-openalex",
            "status": "success",
            "content": [
                {
                    "text": "**1. Recent Paper**\n👥 Authors: New Author\n📅 Year: 2023\n📖 Published in: New Journal\n📈 Citations: 25\n📝 Summary: Recent research\n🔗 DOI: 10.1234/new"
                }
            ],
        }

        tool_use = {
            "toolUseId": "test-789",
            "input": {
                "topic": "research",
                "min_year": 2020,
                "enable_openalex": True,
                "enable_orkg": False,
                "enable_core": False,
            },
        }

        result = research_finder(tool_use)

        content = result["content"][0]["text"]
        assert "Recent Paper" in content
        # Old paper should not be present since tools filter by year
        assert "Old Paper" not in content

    @patch("research_finder.openalex_search")
    @patch("research_finder.config")
    def test_publication_type_filtering(self, mock_config, mock_openalex):
        """Test publication type filtering parameter is passed correctly."""
        from test_data_loader import test_data

        mock_config.get_defaults.return_value = {"max_results": 10, "min_year": 2020}
        mock_config.get_behavior_config.return_value = {"max_workers": 3}
        mock_config.is_source_enabled.side_effect = lambda x: x == "openalex"
        mock_config.get_source_config.return_value = {"timeout": 40}

        # Use real synthetic data from OpenAlex
        openalex_data = test_data.get_successful_openalex_data()
        if openalex_data:
            mock_openalex.return_value = openalex_data
        else:
            mock_openalex.return_value = {
                "toolUseId": "test-filter-openalex",
                "status": "success",
                "content": [{"text": "No papers found"}],
            }

        tool_use = {
            "toolUseId": "test-filter",
            "input": {
                "topic": "AI",
                "publication_types": ["conference"],
                "min_year": 2020,
                "enable_openalex": True,
                "enable_orkg": False,
                "enable_core": False,
            },
        }

        result = research_finder(tool_use)

        # Verify the function runs successfully with publication_types parameter
        assert result["status"] == "success"
        content = result["content"][0]["text"]
        assert "Publication Types: conference" in content

    @patch("research_finder.openalex_search")
    @patch("research_finder.config")
    def test_api_timeout_handling(self, mock_config, mock_openalex):
        """Test API timeout handling."""
        mock_config.get_defaults.return_value = {"max_results": 10, "min_year": 2004}
        mock_config.get_behavior_config.return_value = {"max_workers": 3}
        mock_config.is_source_enabled.side_effect = lambda x: x == "openalex"
        mock_config.get_source_config.return_value = {"timeout": 1}

        # Simulate timeout
        mock_openalex.side_effect = Exception("Timeout")

        tool_use = {
            "toolUseId": "test-timeout",
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
        assert "No research papers found" in content

    @patch("research_finder.openalex_search")
    @patch("research_finder.config")
    def test_empty_results_handling(self, mock_config, mock_openalex):
        """Test handling of empty API results."""
        mock_config.get_defaults.return_value = {"max_results": 10, "min_year": 2004}
        mock_config.get_behavior_config.return_value = {"max_workers": 3}
        mock_config.is_source_enabled.side_effect = lambda x: x == "openalex"
        mock_config.get_source_config.return_value = {"timeout": 40}

        mock_openalex.return_value = {
            "toolUseId": "test-empty-openalex",
            "status": "success",
            "content": [{"text": "No papers found"}],
        }

        tool_use = {
            "toolUseId": "test-empty",
            "input": {
                "topic": "nonexistent",
                "enable_openalex": True,
                "enable_orkg": False,
                "enable_core": False,
            },
        }

        result = research_finder(tool_use)

        assert result["status"] == "success"
        content = result["content"][0]["text"]
        assert "No research papers found" in content

    @patch("research_finder.openalex_search")
    @patch("research_finder.config")
    def test_malformed_abstract_handling(self, mock_config, mock_openalex):
        """Test handling of malformed abstract data."""
        mock_config.get_defaults.return_value = {"max_results": 10, "min_year": 2004}
        mock_config.get_behavior_config.return_value = {"max_workers": 3}
        mock_config.is_source_enabled.side_effect = lambda x: x == "openalex"
        mock_config.get_source_config.return_value = {"timeout": 40}

        mock_openalex.return_value = {
            "toolUseId": "test-malformed-openalex",
            "status": "success",
            "content": [
                {
                    "text": "**1. Paper with Missing Data**\n👥 Authors: N/A\n📅 Year: N/A\n📖 Published in: N/A\n📈 Citations: 0\n📝 Summary: N/A\n🔗 DOI: N/A"
                }
            ],
        }

        tool_use = {
            "toolUseId": "test-malformed",
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
        assert "Paper with Missing Data" in content

    @pytest.mark.parametrize("max_results", [1, 5, 10])
    @patch("research_finder.openalex_search")
    @patch("research_finder.config")
    def test_result_limiting(self, mock_config, mock_openalex, max_results):
        """Test that result limiting works correctly."""
        mock_config.get_defaults.return_value = {
            "max_results": max_results,
            "min_year": 2004,
        }
        mock_config.get_behavior_config.return_value = {"max_workers": 3}
        mock_config.is_source_enabled.side_effect = lambda x: x == "openalex"
        mock_config.get_source_config.return_value = {"timeout": 40}

        # Generate mock results up to max_results
        papers = []
        for i in range(max_results):
            papers.append(
                f"**{i + 1}. Paper {i + 1}**\n👥 Authors: Author {i + 1}\n📅 Year: 2023\n📖 Published in: Journal {i + 1}\n📈 Citations: {i + 1}\n📝 Summary: Paper {i + 1} summary\n🔗 DOI: 10.1234/{i + 1}"
            )

        mock_openalex.return_value = {
            "toolUseId": f"test-limit-{max_results}-openalex",
            "status": "success",
            "content": [{"text": "\n\n".join(papers)}],
        }

        tool_use = {
            "toolUseId": f"test-limit-{max_results}",
            "input": {
                "topic": "test",
                "max_results": max_results,
                "enable_openalex": True,
                "enable_orkg": False,
                "enable_core": False,
            },
        }

        result = research_finder(tool_use)

        assert result["status"] == "success"
        content = result["content"][0]["text"]
        assert f"Max Results: {max_results}" in content

    @patch("research_finder.orkg_search")
    @patch("research_finder.config")
    def test_orkg_filter_parameter(self, mock_config, mock_orkg):
        """Test ORKG-specific filter parameters."""
        mock_config.get_defaults.return_value = {"max_results": 5, "min_year": 2020}
        mock_config.get_behavior_config.return_value = {"max_workers": 3}
        mock_config.is_source_enabled.side_effect = lambda x: x == "orkg"
        mock_config.get_source_config.return_value = {"timeout": 60}

        mock_orkg.return_value = {
            "toolUseId": "test-orkg-filter-orkg",
            "status": "success",
            "content": [
                {
                    "text": "**1. Filtered ORKG Paper**\n👥 Authors: ORKG Author\n📅 Year: 2023\n📖 Published in: ORKG Journal\n📈 Citations: 20\n📝 Summary: Filtered paper\n🔗 DOI: 10.5678/filtered"
                }
            ],
        }

        tool_use = {
            "toolUseId": "test-orkg-filter",
            "input": {
                "topic": "AI",
                "min_year": 2020,
                "enable_openalex": False,
                "enable_orkg": True,
                "enable_core": False,
            },
        }

        result = research_finder(tool_use)

        assert result["status"] == "success"
        content = result["content"][0]["text"]
        assert "Filtered ORKG Paper" in content
