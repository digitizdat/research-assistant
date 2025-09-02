#!/usr/bin/env python3
"""
This agentic workflow inspired by an example from the Strands documentation
implements the following:

Data Sources:
* research_finder tool - Uses OpenAlex and CORE APIs to locate relevant
scientific papers
* Citation analysis - Includes citation counts and summaries
* Web sources - Uses http_request for supplementary web research

Architecture:
* Multi-agent workflow - Research gathering → Analysis → Writing
* Citation verification - Analyst checks citation counts ≥1
* Quality assurance - Analyst verifies claims are supported by research
* Natural language interaction - Conversational interface with history


Priority Improvements

High Priority:
* ORKG Ask integration - Immediate semantic search capability
* Unpaywall integration - OA verification (simple API calls)
* Year-based filtering - Basic query enhancement

Medium Priority:
* OpenCitations - Citation network analysis
* Multi-factor ranking - Combine multiple signals
* Custom FAISS implementation - Only if ORKG Ask insufficient

Low Priority:
* OAI-PMH harvesting - Extended coverage
* Custom embedding generation - Redundant if ORKG Ask works
"""

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor

from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from strands import Agent
from strands_tools import http_request

import research_finder


async def run_research_workflow(user_input):
    """
    Run a parallel multi-agent workflow for research and fact-checking.

    Phase 1: Parallel data gathering (research_finder + web_research)
    Phase 2: Sequential analysis (depends on research results)
    Phase 3: Final report generation

    Args:
        user_input: Research query or claim to verify

    Returns:
        str: The final report from the Writer Agent
    """

    print(f"\nProcessing: '{user_input}'")

    # Phase 1: Parallel Data Gathering
    print("\nPhase 1: Gathering data from multiple sources in parallel...")

    # Create agents for parallel execution
    research_agent = Agent(
        system_prompt=(
            "You are a Research Agent focused on scientific literature. "
            "Use research_finder to find relevant scientific papers. "
            "Include citation counts and paper summaries. "
            "Keep findings under 400 words."
        ),
        callback_handler=None,
        tools=[research_finder],
    )

    web_research_agent = Agent(
        system_prompt=(
            "You are a Web Research Agent focused on current information. "
            "Use http_request to find relevant web sources. "
            "Focus on authoritative sources and recent information. "
            "Keep findings under 300 words."
        ),
        callback_handler=None,
        tools=[http_request],
    )

    # Execute parallel data gathering
    with ThreadPoolExecutor(max_workers=2) as executor:
        research_future = executor.submit(
            research_agent,
            f"Find scientific papers about: '{user_input}'. Limit to 3 papers max.",
        )
        web_future = executor.submit(
            web_research_agent,
            f"Find web information about: '{user_input}'. Use 1 authoritative source.",
        )

        # Wait for both to complete
        research_results = research_future.result()
        web_results = web_future.result()

    print("✓ Parallel data gathering complete")

    # Phase 2: Citation Analysis (depends on research results)
    print("\nPhase 2: Analyzing research quality and citations...")

    analyst_agent = Agent(
        system_prompt=(
            "You are a Citation Analyst that verifies research quality. "
            "1. Check citation counts ≥1 for credibility "
            "2. Verify claims are supported by evidence "
            "3. Rate overall accuracy 1-5 "
            "4. Flag unsupported claims "
            "5. Keep analysis under 400 words"
        ),
        callback_handler=None,
    )

    combined_findings = (
        f"RESEARCH PAPERS:\n{research_results}\n\nWEB SOURCES:\n{web_results}"
    )
    analysis = analyst_agent(
        f"Analyze the quality and credibility of findings about '{user_input}':\n\n{combined_findings}"
    )

    print("✓ Citation analysis complete")

    # Phase 3: Final Report Generation
    print("\nPhase 3: Generating final report...")

    writer_agent = Agent(
        system_prompt=(
            "You are a Report Writer that creates clear, structured reports. "
            "1. Present key findings with source attribution "
            "2. For fact-checks: clearly state true/false "
            "3. Highlight high-citation research "
            "4. Keep reports under 500 words"
        )
    )

    final_report = writer_agent(
        f"Create a comprehensive report on '{user_input}' based on this analysis:\n\n{analysis}"
    )

    print("✓ Report generation complete")
    return final_report


if __name__ == "__main__":
    # Print welcome message
    print("\nAgentic Workflow: Research Assistant\n")
    print("This demo shows Strands agents in a workflow with web research.")
    print("Try research questions or fact-check claims.")
    print("\nExamples:")
    print('- "What are quantum computers?"')
    print('- "Lemon cures cancer"')
    print('- "Tuesday comes before Monday in the week"')

    # Interactive loop with prompt-toolkit
    history = FileHistory(".research_history")

    # Detect editing mode preference
    editing_mode = os.getenv("EDITOR", "vi").lower()
    use_vi_mode = "vi" in editing_mode or "vim" in editing_mode

    print(
        f"\nUsing {'Vi' if use_vi_mode else 'Emacs'} editing mode (set EDITOR env var to change)"
    )

    while True:
        try:
            user_input = prompt("\n> ", history=history, vi_mode=use_vi_mode)
            if user_input.lower() == "exit":
                print("\nGoodbye!")
                break

            # Process the input through the parallel workflow
            final_report = asyncio.run(run_research_workflow(user_input))
        except (KeyboardInterrupt, EOFError):
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            print("Please try a different request.")
