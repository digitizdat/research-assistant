"""Tests for configuration management tool."""

import os
import tempfile

import pytest

from config_manager import ConfigManager
from config_tool import ConfigTool, config_manager


@pytest.fixture
def temp_config():
    """Create a temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("""
sources:
  openalex:
    enabled: true
    timeout: 40
  orkg:
    enabled: false
    timeout: 60
    max_retries: 3
  core:
    enabled: true
    timeout: 30
    max_retries: 2
""")
        temp_path = f.name

    yield temp_path
    os.unlink(temp_path)


def test_enable_tool(temp_config):
    """Test enabling a tool."""
    tool = ConfigTool()
    tool.config_manager = ConfigManager(temp_config)
    tool.config = tool.config_manager.load_config()

    result = tool.process_command("enable orkg tool")
    assert "ORKG tool enabled" in result
    assert tool.config["sources"]["orkg"]["enabled"] is True


def test_disable_tool(temp_config):
    """Test disabling a tool."""
    tool = ConfigTool()
    tool.config_manager = ConfigManager(temp_config)
    tool.config = tool.config_manager.load_config()

    result = tool.process_command("disable openalex")
    assert "OPENALEX tool disabled" in result
    assert tool.config["sources"]["openalex"]["enabled"] is False


def test_set_timeout(temp_config):
    """Test setting timeout for a tool."""
    tool = ConfigTool()
    tool.config_manager = ConfigManager(temp_config)
    tool.config = tool.config_manager.load_config()

    result = tool.process_command("set orkg timeout to 90")
    assert "ORKG timeout set to 90 seconds" in result
    assert tool.config["sources"]["orkg"]["timeout"] == 90


def test_set_retries(temp_config):
    """Test setting retries for a tool."""
    tool = ConfigTool()
    tool.config_manager = ConfigManager(temp_config)
    tool.config = tool.config_manager.load_config()

    result = tool.process_command("set core retries to 5")
    assert "CORE retries set to 5" in result
    assert tool.config["sources"]["core"]["max_retries"] == 5


def test_show_config(temp_config):
    """Test showing configuration."""
    tool = ConfigTool()
    tool.config_manager = ConfigManager(temp_config)
    tool.config = tool.config_manager.load_config()

    result = tool.process_command("show config")
    assert "Current Configuration:" in result
    assert "OPENALEX: enabled" in result
    assert "ORKG: disabled" in result
    assert "CORE: enabled" in result


def test_unknown_command():
    """Test handling unknown commands."""
    tool = ConfigTool()
    result = tool.process_command("invalid command")
    assert "Unknown command" in result


def test_config_manager_function():
    """Test the standalone config_manager function."""
    result = config_manager("show config")
    assert "Current Configuration:" in result
