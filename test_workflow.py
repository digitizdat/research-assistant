import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from research_agents_workflow import run_research_workflow


@pytest.mark.asyncio
@patch("research_agents_workflow.Agent")
@patch("research_agents_workflow.ThreadPoolExecutor")
async def test_run_research_workflow(mock_executor, mock_agent):
    """Test the basic workflow execution."""
    # Mock agent responses
    mock_research_agent = Mock()
    mock_research_agent.return_value = "Research findings"

    mock_web_agent = Mock()
    mock_web_agent.return_value = "Web findings"

    mock_analyst_agent = Mock()
    mock_analyst_agent.return_value = "Analysis results"

    mock_writer_agent = Mock()
    mock_writer_agent.return_value = "Final report"

    mock_agent.side_effect = [
        mock_research_agent,
        mock_web_agent,
        mock_analyst_agent,
        mock_writer_agent,
    ]

    # Mock ThreadPoolExecutor
    mock_executor_instance = Mock()
    mock_future = Mock()
    mock_future.result.return_value = "Mock result"
    mock_executor_instance.submit.return_value = mock_future
    mock_executor.return_value.__enter__.return_value = mock_executor_instance

    result = await run_research_workflow("test query")

    assert result == "Final report"
    assert mock_agent.call_count == 4


@pytest.mark.asyncio
async def test_workflow_with_empty_input():
    """Test workflow handles empty input gracefully."""
    with patch("research_agents_workflow.Agent") as mock_agent:
        mock_agent.return_value.return_value = "Empty response"

        with patch("research_agents_workflow.ThreadPoolExecutor"):
            result = await run_research_workflow("")
            assert isinstance(result, str)
