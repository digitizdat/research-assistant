"""Functional tests for research_finder tool."""
import pytest
from unittest.mock import Mock, patch
from research_finder import research_finder


class TestResearchFinderFunctional:
    """Functional tests for research_finder tool."""

    def test_openalex_response_parsing(self):
        """Test OpenAlex response parsing with real-like data."""
        with patch("requests.get") as mock_get:
            # Mock OpenAlex response with inverted index abstract
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "results": [
                    {
                        "title": "Deep Learning for Computer Vision",
                        "authorships": [
                            {"author": {"display_name": "John Smith"}},
                            {"author": {"display_name": "Jane Doe"}}
                        ],
                        "publication_year": 2021,
                        "host_venue": {"display_name": "Nature Machine Intelligence"},
                        "doi": "10.1038/s42256-021-00123-4",
                        "abstract_inverted_index": {
                            "Deep": [0], "learning": [1], "has": [2], 
                            "revolutionized": [3], "computer": [4], "vision": [5]
                        },
                        "relevance_score": 0.95,
                        "cited_by_count": 150,
                        "type": "journal-article"
                    }
                ]
            }
            mock_get.return_value = mock_response

            tool_use = {
                "toolUseId": "test-123",
                "input": {"topic": "deep learning", "max_results": 2}
            }

            result = research_finder(tool_use)

            assert result["status"] == "success"
            content = result["content"][0]["text"]
            assert "Deep Learning for Computer Vision" in content
            assert "John Smith, Jane Doe" in content
            assert "Nature Machine Intelligence" in content
            assert "Citations: 150" in content
            assert "Deep learning has revolutionized computer vision" in content

    def test_orkg_response_parsing(self):
        """Test ORKG response parsing with spec-compliant data."""
        with patch("requests.get") as mock_get:
            # Mock responses: OpenAlex fails, ORKG succeeds
            def side_effect(url, **kwargs):
                mock_response = Mock()
                if "openalex" in url:
                    mock_response.status_code = 500
                    return mock_response
                else:  # ORKG
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "uuid": "test-uuid",
                        "timestamp": "2024-01-01T00:00:00Z",
                        "payload": {
                            "items": [
                                {
                                    "id": "12345",
                                    "title": "AI Ethics in Healthcare",
                                    "authors": ["Dr. Alice Brown", "Prof. Bob Wilson"],
                                    "year": 2022,
                                    "journals": ["AI Ethics Journal"],
                                    "doi": "10.1007/s43681-022-00123-4",
                                    "abstract": "This paper explores ethical considerations in AI healthcare applications.",
                                    "citation_count": 45,
                                    "document_type": "journal"
                                }
                            ],
                            "total_hits": 1,
                            "has_more": False
                        }
                    }
                    return mock_response

            mock_get.side_effect = side_effect

            tool_use = {
                "toolUseId": "test-456",
                "input": {"topic": "AI ethics", "max_results": 2, "min_year": 2020}
            }

            result = research_finder(tool_use)

            assert result["status"] == "success"
            content = result["content"][0]["text"]
            assert "AI Ethics in Healthcare" in content
            assert "Dr. Alice Brown, Prof. Bob Wilson" in content
            assert "AI Ethics Journal" in content
            assert "Citations: 45" in content

    def test_year_filtering(self):
        """Test that year filtering works correctly."""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "results": [
                    {
                        "title": "Old Paper",
                        "authorships": [{"author": {"display_name": "Old Author"}}],
                        "publication_year": 2010,  # Should be filtered out
                        "host_venue": {"display_name": "Old Journal"},
                        "doi": "10.1234/old",
                        "abstract_inverted_index": {"old": [0], "research": [1]},
                        "relevance_score": 0.8,
                        "cited_by_count": 50,
                        "type": "journal-article"
                    },
                    {
                        "title": "Recent Paper",
                        "authorships": [{"author": {"display_name": "New Author"}}],
                        "publication_year": 2023,  # Should be included
                        "host_venue": {"display_name": "New Journal"},
                        "doi": "10.1234/new",
                        "abstract_inverted_index": {"recent": [0], "research": [1]},
                        "relevance_score": 0.9,
                        "cited_by_count": 25,
                        "type": "journal-article"
                    }
                ]
            }
            mock_get.return_value = mock_response

            tool_use = {
                "toolUseId": "test-789",
                "input": {"topic": "research", "min_year": 2020}
            }

            result = research_finder(tool_use)

            content = result["content"][0]["text"]
            assert "Recent Paper" in content
            assert "Old Paper" not in content

    def test_publication_type_filtering(self):
        """Test publication type filtering."""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "results": [
                    {
                        "title": "Conference Paper",
                        "authorships": [{"author": {"display_name": "Conf Author"}}],
                        "publication_year": 2023,
                        "host_venue": {"display_name": "ML Conference"},
                        "doi": "10.1234/conf",
                        "abstract_inverted_index": {"conference": [0], "paper": [1]},
                        "relevance_score": 0.9,
                        "cited_by_count": 15,
                        "type": "conference-paper"
                    },
                    {
                        "title": "Book Chapter",
                        "authorships": [{"author": {"display_name": "Book Author"}}],
                        "publication_year": 2023,
                        "host_venue": {"display_name": "AI Handbook"},
                        "doi": "10.1234/book",
                        "abstract_inverted_index": {"book": [0], "chapter": [1]},
                        "relevance_score": 0.8,
                        "cited_by_count": 30,
                        "type": "book-chapter"
                    }
                ]
            }
            mock_get.return_value = mock_response

            tool_use = {
                "toolUseId": "test-filter",
                "input": {
                    "topic": "AI",
                    "publication_types": ["conference"],
                    "min_year": 2020
                }
            }

            result = research_finder(tool_use)

            content = result["content"][0]["text"]
            assert "Conference Paper" in content
            assert "Book Chapter" not in content

    def test_api_timeout_handling(self):
        """Test handling of API timeouts."""
        with patch("requests.get") as mock_get:
            # Simulate timeout
            mock_get.side_effect = Exception("Timeout")

            tool_use = {
                "toolUseId": "test-timeout",
                "input": {"topic": "timeout test"}
            }

            result = research_finder(tool_use)

            assert result["status"] == "success"
            content = result["content"][0]["text"]
            assert "No research papers found" in content

    def test_empty_results_handling(self):
        """Test handling when APIs return no results."""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"results": []}
            mock_get.return_value = mock_response

            tool_use = {
                "toolUseId": "test-empty",
                "input": {"topic": "nonexistent topic"}
            }

            result = research_finder(tool_use)

            assert result["status"] == "success"
            content = result["content"][0]["text"]
            assert "No research papers found" in content
            assert "Try broadening your search terms" in content

    def test_malformed_abstract_handling(self):
        """Test handling of malformed abstract data."""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "results": [
                    {
                        "title": "Paper with Empty Abstract",
                        "authorships": [{"author": {"display_name": "Test Author"}}],
                        "publication_year": 2023,
                        "host_venue": {"display_name": "Test Journal"},
                        "doi": "10.1234/test",
                        "abstract_inverted_index": {},  # Empty abstract
                        "relevance_score": 0.8,
                        "cited_by_count": 10,
                        "type": "journal-article"
                    }
                ]
            }
            mock_get.return_value = mock_response

            tool_use = {
                "toolUseId": "test-malformed",
                "input": {"topic": "test"}
            }

            result = research_finder(tool_use)

            assert result["status"] == "success"
            content = result["content"][0]["text"]
            assert "Paper with Empty Abstract" in content
            # Should handle empty abstract gracefully

    @pytest.mark.parametrize("max_results", [1, 5, 10])
    def test_result_limiting(self, max_results):
        """Test that result limiting works correctly."""
        with patch("requests.get") as mock_get:
            # Create more results than requested
            results = []
            for i in range(15):  # More than any max_results
                results.append({
                    "title": f"Paper {i+1}",
                    "authorships": [{"author": {"display_name": f"Author {i+1}"}}],
                    "publication_year": 2023,
                    "host_venue": {"display_name": f"Journal {i+1}"},
                    "doi": f"10.1234/paper{i+1}",
                    "abstract_inverted_index": {"test": [0], "paper": [1]},
                    "relevance_score": 0.8,
                    "cited_by_count": 10,
                    "type": "journal-article"
                })

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"results": results}
            mock_get.return_value = mock_response

            tool_use = {
                "toolUseId": f"test-limit-{max_results}",
                "input": {"topic": "test", "max_results": max_results}
            }

            result = research_finder(tool_use)

            content = result["content"][0]["text"]
            # Count occurrences of paper titles
            paper_count = content.count("Paper ")
            assert paper_count <= max_results

    def test_orkg_filter_parameter(self):
        """Test ORKG year filter parameter construction."""
        with patch("requests.get") as mock_get:
            def check_params(url, params=None, **kwargs):
                if "orkg" in url and params:
                    # Verify filter parameter is correctly constructed
                    assert "filter" in params
                    assert "year >= 2020" in params["filter"]
                
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "payload": {"items": []}
                }
                return mock_response

            mock_get.side_effect = check_params

            tool_use = {
                "toolUseId": "test-orkg-filter",
                "input": {"topic": "test", "min_year": 2020}
            }

            result = research_finder(tool_use)
            assert result["status"] == "success"