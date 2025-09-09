"""
Test data loader utility for accessing synthetic test data.
"""

import json
from pathlib import Path
from typing import Any, Dict


class SyntheticDataLoader:
    """Loads and provides access to synthetic test data."""

    def __init__(self):
        self.test_dir = Path(__file__).parent
        self._openalex_data = None
        self._orkg_data = None
        self._core_data = None

    @property
    def openalex_data(self) -> Dict[str, Any]:
        """Lazy load OpenAlex test data."""
        if self._openalex_data is None:
            with open(self.test_dir / "openalex_test_data.json") as f:
                self._openalex_data = json.load(f)
        return self._openalex_data

    @property
    def orkg_data(self) -> Dict[str, Any]:
        """Lazy load ORKG test data."""
        if self._orkg_data is None:
            with open(self.test_dir / "orkg_test_data.json") as f:
                self._orkg_data = json.load(f)
        return self._orkg_data

    @property
    def core_data(self) -> Dict[str, Any]:
        """Lazy load CORE test data."""
        if self._core_data is None:
            with open(self.test_dir / "core_test_data.json") as f:
                self._core_data = json.load(f)
        return self._core_data

    def get_openalex_data(self, query: str) -> Dict[str, Any]:
        """Get OpenAlex test data for a query."""
        return self.openalex_data.get(query, {})

    def get_orkg_data(self, query: str) -> Dict[str, Any]:
        """Get ORKG test data for a query."""
        return self.orkg_data.get(query, {})

    def get_core_data(self, query: str) -> Dict[str, Any]:
        """Get CORE test data for a query."""
        return self.core_data.get(query, {})

    def get_successful_openalex_data(self) -> Dict[str, Any]:
        """Get first successful OpenAlex response."""
        for query, data in self.openalex_data.items():
            if data.get("status") == "success" and "Found" in data.get("content", [{}])[
                0
            ].get("text", ""):
                return data
        return {}

    def get_successful_orkg_data(self) -> Dict[str, Any]:
        """Get first successful ORKG response."""
        for query, data in self.orkg_data.items():
            if data.get("status") == "success" and "Found" in data.get("content", [{}])[
                0
            ].get("text", ""):
                return data
        return {}

    def get_successful_core_data(self) -> Dict[str, Any]:
        """Get first successful CORE response."""
        for query, data in self.core_data.items():
            if data.get("status") == "success" and "Found" in data.get("content", [{}])[
                0
            ].get("text", ""):
                return data
        return {}


# Global instance for easy access
test_data = SyntheticDataLoader()
