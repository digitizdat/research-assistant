"""Tests for configuration management."""

import tempfile
from pathlib import Path

import yaml

from config_manager import ConfigManager


class TestConfigManager:
    """Test configuration management functionality."""

    def test_load_default_config(self):
        """Test loading default configuration when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "nonexistent.yaml"
            config_mgr = ConfigManager(config_path)

            config_data = config_mgr.load_config()

            assert "sources" in config_data
            assert "defaults" in config_data
            assert "behavior" in config_data

    def test_load_yaml_config(self):
        """Test loading configuration from YAML file."""
        test_config = {
            "sources": {
                "openalex": {"enabled": False, "timeout": 30},
                "orkg": {"enabled": True, "timeout": 45},
            },
            "defaults": {"max_results": 5, "min_year": 2020},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(test_config, f)
            config_path = f.name

        try:
            config_mgr = ConfigManager(config_path)
            loaded_config = config_mgr.load_config()

            assert loaded_config["sources"]["openalex"]["enabled"] is False
            assert loaded_config["sources"]["orkg"]["timeout"] == 45
            assert loaded_config["defaults"]["max_results"] == 5
        finally:
            Path(config_path).unlink()

    def test_source_config_access(self):
        """Test accessing source-specific configuration."""
        config_mgr = ConfigManager()

        openalex_config = config_mgr.get_source_config("openalex")
        assert isinstance(openalex_config, dict)

        orkg_config = config_mgr.get_source_config("orkg")
        assert isinstance(orkg_config, dict)

    def test_source_enabled_check(self):
        """Test checking if sources are enabled."""
        config_mgr = ConfigManager()

        # Should return True for enabled sources
        assert config_mgr.is_source_enabled("openalex") is True
        assert config_mgr.is_source_enabled("orkg") is True

        # Should return True for unknown sources (default)
        assert config_mgr.is_source_enabled("unknown") is True

    def test_get_defaults(self):
        """Test getting default parameters."""
        config_mgr = ConfigManager()

        defaults = config_mgr.get_defaults()

        assert "max_results" in defaults
        assert "min_year" in defaults
        assert "publication_types" in defaults
        assert isinstance(defaults["publication_types"], list)

    def test_get_behavior_config(self):
        """Test getting behavior configuration."""
        config_mgr = ConfigManager()

        behavior = config_mgr.get_behavior_config()

        assert isinstance(behavior, dict)
        # Should have some behavior settings
        assert len(behavior) > 0

    def test_config_caching(self):
        """Test that configuration is cached after first load."""
        config_mgr = ConfigManager()

        # Load config twice
        config1 = config_mgr.load_config()
        config2 = config_mgr.load_config()

        # Should be the same object (cached)
        assert config1 is config2
