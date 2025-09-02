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

import os
from prompt_toolkit import prompt
from prompt_toolkit.application.current import get_app
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from strands import Agent
from strands_tools import http_request

import research_finder


def run_research_workflow(user_input):
    """
    Run a multi-agent workflow for research and fact-checking with web sources.
    Shows progress, but presents only the final report to the user.

    Args:
        user_input: Research query or claim to verify

    Returns:
        str: The final report from the Writer Agent
    """

    print(f"\nProcessing: '{user_input}'")

    # Step 1: Research Gathering Agent with enhanced web capabilities
    print("\nStep 1: Research Gathering Agent gathering information...")

    research_gathering_agent = Agent(
        system_prompt=(
            "You are a Research Gathering Agent that collects information from web and scientific sources. "
            "1. Use research_finder for scientific studies, including summaries and citation counts "
            "2. Use http_request for web sources "
            "3. Always include citation counts and paper summaries when available "
            "4. Keep findings under 500 words"
        ),
        callback_handler=None,
        tools=[http_request, research_finder],
    )

    researcher_response = research_gathering_agent(
        f"Research: '{user_input}'. Use research_finder (limit to 3 papers max) for scientific studies, "
        f"and http_request (1 source max) for web sources. Keep all responses concise.",
    )

    # Extract only the relevant content from the researcher response
    research_findings = str(researcher_response)

    print("Research complete")
    print("Passing research findings to Analyst Agent...\n")

    # Step 2: Analyst Agent to verify facts
    print("Step 2: Analyst Agent analyzing findings...")

    analyst_agent = Agent(
        system_prompt=(
            "You are an Analyst Agent that verifies information quality. "
            "1. Verify that research papers cited have at least 1 citation (if data provided) "
            "2. Check that claims are supported by cited research papers "
            "3. Rate accuracy from 1-5 and identify key insights "
            "4. Flag any unsupported claims or low-citation research "
            "5. Keep analysis under 400 words"
        ),
        callback_handler=None,
    )

    analyst_response = analyst_agent(
        f"Analyze these findings about '{user_input}':\n\n{research_findings}",
    )

    # Extract only the relevant content from the analyst response
    analysis = str(analyst_response)

    print("Analysis complete")
    print("Passing analysis to Writer Agent...\n")

    # Step 3: Writer Agent to create report
    print("Step 3: Writer Agent creating final report...")

    writer_agent = Agent(
        system_prompt=(
            "You are a Writer Agent that creates clear reports. "
            "1. For fact-checks: State whether claims are true or false "
            "2. For research: Present key insights in a logical structure "
            "3. Keep reports under 500 words with brief source mentions"
        )
    )

    # Execute the Writer Agent with the analysis (output is shown to user)
    final_report = writer_agent(
        f"Create a report on '{user_input}' based on this analysis:\n\n{analysis}"
    )

    print("Report creation complete")

    # Return the final report
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
    editing_mode = os.getenv('EDITOR', 'vi').lower()
    use_vi_mode = 'vi' in editing_mode or 'vim' in editing_mode
    
    print(f"\nUsing {'Vi' if use_vi_mode else 'Emacs'} editing mode (set EDITOR env var to change)")
    
    while True:
        try:
            user_input = prompt(
                "\n> ",
                history=history,
                vi_mode=use_vi_mode
            )
            if user_input.lower() == "exit":
                print("\nGoodbye!")
                break

            # Process the input through the workflow of agents
            final_report = run_research_workflow(user_input)
        except (KeyboardInterrupt, EOFError):
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            print("Please try a different request.")
