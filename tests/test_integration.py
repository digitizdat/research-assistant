"""Integration tests for the research workflow."""
import pytest
from unittest.mock import Mock, patch
import asyncio
from research_agents_workflow import run_research_workflow


class TestWorkflowIntegration:
    """Integration tests for the complete research workflow."""

    @pytest.mark.asyncio
    async def test_workflow_with_research_finder(self):
        """Test complete workflow with mocked research_finder responses."""
        with patch("research_agents_workflow.Agent") as mock_agent_class:
            with patch("research_finder.research_finder") as mock_research_finder:
                # Mock research_finder to return realistic data
                mock_research_finder.return_value = {
                    "toolUseId": "test-123",
                    "status": "success",
                    "content": [{
                        "text": "Found 2 papers: 'AI in Medicine' (Citations: 150) and 'ML for Diagnosis' (Citations: 89)"
                    }]
                }

                # Mock agents
                research_agent = Mock()
                research_agent.return_value = "Research findings from scientific papers"
                
                web_agent = Mock()
                web_agent.return_value = "Web research findings"
                
                analyst_agent = Mock()
                analyst_agent.return_value = "Analysis: High quality papers with good citations"
                
                writer_agent = Mock()
                writer_agent.return_value = "Final comprehensive report"

                mock_agent_class.side_effect = [
                    research_agent, web_agent, analyst_agent, writer_agent
                ]

                # Mock ThreadPoolExecutor
                with patch("research_agents_workflow.ThreadPoolExecutor") as mock_executor:
                    mock_executor_instance = Mock()
                    mock_future = Mock()
                    mock_future.result.return_value = "Mock result"
                    mock_executor_instance.submit.return_value = mock_future
                    mock_executor.return_value.__enter__.return_value = mock_executor_instance

                    result = await run_research_workflow("AI in healthcare")

                    assert result == "Final comprehensive report"
                    assert mock_agent_class.call_count == 4
                    
                    # Verify research agent was called with research_finder tool
                    research_agent_call = mock_agent_class.call_args_list[0]
                    assert "research_finder" in str(research_agent_call)

    @pytest.mark.asyncio
    async def test_workflow_error_handling(self):
        """Test workflow handles research_finder errors gracefully."""
        with patch("research_agents_workflow.Agent") as mock_agent_class:
            # Mock agents that handle errors
            research_agent = Mock()
            research_agent.return_value = "No research papers found due to API issues"
            
            web_agent = Mock()
            web_agent.return_value = "Limited web information available"
            
            analyst_agent = Mock()
            analyst_agent.return_value = "Analysis: Limited data available, low confidence"
            
            writer_agent = Mock()
            writer_agent.return_value = "Report: Insufficient data for comprehensive analysis"

            mock_agent_class.side_effect = [
                research_agent, web_agent, analyst_agent, writer_agent
            ]

            with patch("research_agents_workflow.ThreadPoolExecutor") as mock_executor:
                mock_executor_instance = Mock()
                mock_future = Mock()
                mock_future.result.return_value = "Error result"
                mock_executor_instance.submit.return_value = mock_future
                mock_executor.return_value.__enter__.return_value = mock_executor_instance

                result = await run_research_workflow("nonexistent topic")

                assert isinstance(result, str)
                assert len(result) > 0  # Should still return some result

    @pytest.mark.asyncio
    async def test_workflow_with_filtering(self):
        """Test workflow handles research_finder integration."""
        with patch("research_agents_workflow.Agent") as mock_agent_class:
            # Mock agents with simple responses
            research_agent = Mock()
            research_agent.return_value = "Research findings with filtering"
            
            web_agent = Mock()
            web_agent.return_value = "Web findings"
            
            analyst_agent = Mock()
            analyst_agent.return_value = "Analysis complete"
            
            writer_agent = Mock()
            writer_agent.return_value = "Final filtered report"

            mock_agent_class.side_effect = [
                research_agent, web_agent, analyst_agent, writer_agent
            ]

            with patch("research_agents_workflow.ThreadPoolExecutor") as mock_executor:
                mock_executor_instance = Mock()
                mock_future = Mock()
                mock_future.result.return_value = "Mock result"
                mock_executor_instance.submit.return_value = mock_future
                mock_executor.return_value.__enter__.return_value = mock_executor_instance

                result = await run_research_workflow("AI research filtering")

                assert result == "Final filtered report"
                assert mock_agent_class.call_count == 4