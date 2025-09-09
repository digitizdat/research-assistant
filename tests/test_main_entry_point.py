"""Functional tests for main entry point workflow."""

from unittest.mock import MagicMock, patch

import pytest

from research_agents_workflow import run_research_workflow


@pytest.mark.asyncio
@patch("research_agents_workflow.Agent")
async def test_config_command_routing(mock_agent_class):
    """Test configuration commands are handled correctly through main workflow."""
    # Mock agent that returns config response
    mock_agent = MagicMock()
    mock_agent.return_value = "ORKG tool enabled"
    mock_agent_class.return_value = mock_agent

    await run_research_workflow("enable orkg tool")

    # Verify agent was called with config command
    mock_agent.assert_called()
    call_args = mock_agent.call_args[0][0]
    assert "enable orkg tool" in call_args


@pytest.mark.asyncio
@patch("research_agents_workflow.Agent")
async def test_research_query_routing(mock_agent_class):
    """Test research queries are handled correctly through main workflow."""
    # Mock agents for research and web search
    mock_research_agent = MagicMock()
    mock_research_agent.return_value = "Research results about machine learning"
    mock_web_agent = MagicMock()
    mock_web_agent.return_value = "Web results about machine learning"
    mock_analyst_agent = MagicMock()
    mock_analyst_agent.return_value = "Analysis complete"
    mock_writer_agent = MagicMock()
    mock_writer_agent.return_value = "Final report"

    mock_agent_class.side_effect = [
        mock_research_agent,
        mock_web_agent,
        mock_analyst_agent,
        mock_writer_agent,
    ]

    result = await run_research_workflow("machine learning algorithms")

    # Verify research agent was called with research query
    mock_research_agent.assert_called_with("machine learning algorithms")
    assert result == "Final report"


@pytest.mark.asyncio
@patch("research_agents_workflow.Agent")
async def test_show_config_command(mock_agent_class):
    """Test show config command works through main workflow."""
    mock_agent = MagicMock()
    mock_agent.return_value = "Current Configuration:\n  OPENALEX: enabled"
    mock_agent_class.return_value = mock_agent

    result = await run_research_workflow("show config")

    # Config commands are handled directly by config agent
    mock_agent.assert_called_with("show config")
    assert "Current Configuration" in result


@pytest.mark.asyncio
@patch("research_agents_workflow.Agent")
async def test_timeout_config_command(mock_agent_class):
    """Test timeout configuration command works through main workflow."""
    mock_agent = MagicMock()
    mock_agent.return_value = "ORKG timeout set to 90 seconds"
    mock_agent_class.return_value = mock_agent

    result = await run_research_workflow("set orkg timeout to 90")

    # Config commands are handled directly by config agent
    mock_agent.assert_called_with("set orkg timeout to 90")
    assert "timeout set to 90" in result
