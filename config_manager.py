"""Configuration management for research tools."""
from pathlib import Path
from typing import Any, Dict

import yaml


class ConfigManager:
    """Manages configuration loading and access."""

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"
        self.config_path = config_path
        self._config = None

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if self._config is None:
            try:
                with open(self.config_path, 'r') as f:
                    self._config = yaml.safe_load(f)
            except FileNotFoundError:
                # Fallback to default config
                self._config = self._get_default_config()
        return self._config

    def get_source_config(self, source_name: str) -> Dict[str, Any]:
        """Get configuration for a specific source."""
        config = self.load_config()
        return config.get("sources", {}).get(source_name, {})

    def is_source_enabled(self, source_name: str) -> bool:
        """Check if a source is enabled."""
        source_config = self.get_source_config(source_name)
        return source_config.get("enabled", True)

    def get_defaults(self) -> Dict[str, Any]:
        """Get default search parameters."""
        config = self.load_config()
        return config.get("defaults", {})

    def get_behavior_config(self) -> Dict[str, Any]:
        """Get behavior configuration."""
        config = self.load_config()
        return config.get("behavior", {})

    def _get_default_config(self) -> Dict[str, Any]:
        """Fallback default configuration."""
        return {
            "sources": {
                "openalex": {"enabled": True, "timeout": 40},
                "orkg": {"enabled": True, "timeout": 60, "retry_attempts": 3}
            },
            "defaults": {
                "max_results": 10,
                "min_year": 2004,
                "publication_types": ["journal", "conference"]
            },
            "behavior": {
                "parallel_execution": True,
                "max_workers": 2
            }
        }


# Global config instance
config = ConfigManager()
