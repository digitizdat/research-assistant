#!/usr/bin/env python3
"""
Generate CORE test data specifically.
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core_tool import core_search


def generate_core_data():
    """Generate CORE test data with different queries."""
    print("🌐 Generating CORE test data...")
    
    queries = [
        "open access",
        "computer science education", 
        "software engineering",
        "information systems"
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


def save_core_data():
    """Generate and save CORE test data."""
    core_data = generate_core_data()
    
    # Save to tests directory
    output_file = Path(__file__).parent / "tests" / "core_test_data.json"
    with open(output_file, 'w') as f:
        json.dump(core_data, f, indent=2)
    
    print(f"💾 Saved CORE test data to: {output_file}")
    print("🎉 CORE test data generation complete!")
    
    return core_data


if __name__ == "__main__":
    save_core_data()