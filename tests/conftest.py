import sys
from pathlib import Path

import pytest

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_tool_use():
    """Sample tool use fixture for testing."""
    return {
        "toolUseId": "test-fixture-123",
        "input": {
            "topic": "machine learning",
            "max_results": 5,
            "publication_types": ["journal", "conference"],
            "min_year": 2020,
        },
    }


@pytest.fixture
def mock_openalex_response():
    """Mock OpenAlex API response."""
    return {
        "results": [
            {
                "title": "Machine Learning Fundamentals",
                "authorships": [{"author": {"display_name": "John Doe"}}],
                "publication_year": 2021,
                "host_venue": {"display_name": "ML Journal"},
                "doi": "10.1234/ml.2021",
                "abstract_inverted_index": {"machine": [0], "learning": [1]},
                "relevance_score": 0.95,
                "cited_by_count": 150,
                "type": "journal-article",
            }
        ]
    }


@pytest.fixture
def mock_orkg_response():
    """Mock ORKG Ask API response."""
    return {
        "payload": {
            "items": [
                {
                    "title": "AI Decision Making",
                    "authors": ["Jane Smith"],
                    "year": "2022",
                    "venue": "AI Conference",
                    "doi": "10.5678/ai.2022",
                    "abstract": "Study on AI decision making",
                    "score": 0.88,
                    "citation_count": 75,
                }
            ]
        }
    }
