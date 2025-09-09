#!/usr/bin/env python3
"""
Generate synthetic test data by calling actual research tools.
This creates reusable mock data for testing without hitting APIs during tests.
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from openalex_tool import openalex_search
from orkg_tool import orkg_search
from core_tool import core_search


def generate_openalex_data():
    """Generate OpenAlex test data."""
    print("Generating OpenAlex test data...")
    
    queries = [
        "machine learning",
        "artificial intelligence",
        "deep learning computer vision",
        "natural language processing"
    ]
    
    openalex_data = {}
    
    for query in queries:
        tool_use = {
            "toolUseId": f"test-openalex-{query.replace(' ', '-')}",
            "input": {
                "topic": query,
                "max_results": 3,
                "min_year": 2020
            }
        }
        
        try:
            result = openalex_search(tool_use)
            openalex_data[query] = result
            print(f"✓ Generated data for: {query}")
        except Exception as e:
            print(f"✗ Failed for {query}: {e}")
            openalex_data[query] = {
                "toolUseId": tool_use["toolUseId"],
                "status": "error",
                "content": [{"text": f"Error: {str(e)}"}]
            }
    
    return openalex_data


def generate_orkg_data():
    """Generate ORKG Ask test data."""
    print("Generating ORKG Ask test data...")
    
    queries = [
        "machine learning",
        "artificial intelligence ethics",
        "neural networks",
        "computer vision"
    ]
    
    orkg_data = {}
    
    for query in queries:
        tool_use = {
            "toolUseId": f"test-orkg-{query.replace(' ', '-')}",
            "input": {
                "topic": query,
                "max_results": 3,
                "min_year": 2020
            }
        }
        
        try:
            result = orkg_search(tool_use)
            orkg_data[query] = result
            print(f"✓ Generated data for: {query}")
        except Exception as e:
            print(f"✗ Failed for {query}: {e}")
            orkg_data[query] = {
                "toolUseId": tool_use["toolUseId"],
                "status": "error",
                "content": [{"text": f"Error: {str(e)}"}]
            }
    
    return orkg_data


def generate_core_data():
    """Generate CORE test data."""
    print("Generating CORE test data...")
    
    queries = [
        "machine learning",
        "artificial intelligence",
        "data science",
        "computer science"
    ]
    
    core_data = {}
    
    for query in queries:
        tool_use = {
            "toolUseId": f"test-core-{query.replace(' ', '-')}",
            "input": {
                "topic": query,
                "max_results": 3,
                "min_year": 2020
            }
        }
        
        try:
            result = core_search(tool_use)
            core_data[query] = result
            print(f"✓ Generated data for: {query}")
        except Exception as e:
            print(f"✗ Failed for {query}: {e}")
            core_data[query] = {
                "toolUseId": tool_use["toolUseId"],
                "status": "error", 
                "content": [{"text": f"Error: {str(e)}"}]
            }
    
    return core_data


def save_test_data():
    """Generate and save all test data."""
    print("🔬 Generating synthetic test data for research tools...")
    
    # Generate data from each service
    openalex_data = generate_openalex_data()
    orkg_data = generate_orkg_data()
    core_data = generate_core_data()
    
    # Combine into test dataset
    test_data = {
        "openalex": openalex_data,
        "orkg": orkg_data,
        "core": core_data,
        "metadata": {
            "generated_at": "2025-01-01T00:00:00Z",
            "description": "Synthetic test data generated from actual API calls",
            "usage": "Use this data for mocking in tests to avoid API calls"
        }
    }
    
    # Save to tests directory
    output_file = Path(__file__).parent / "tests" / "synthetic_test_data.json"
    with open(output_file, 'w') as f:
        json.dump(test_data, f, indent=2)
    
    print(f"💾 Saved test data to: {output_file}")
    print("🎉 Test data generation complete!")
    
    return test_data


if __name__ == "__main__":
    save_test_data()