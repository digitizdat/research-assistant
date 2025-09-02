# Research Assistant

This agentic workflow inspired by an example from the [Strands
documentation](https://github.com/strands-agents/docs/blob/main/docs/examples/python/agents_workflow.py)
implements the following:

### Data Sources:
* research_finder tool - Uses OpenAlex and CORE APIs to locate relevant
scientific papers
* Citation analysis - Includes citation counts and summaries
* Web sources - Uses http_request for supplementary web research

### Architecture:
* Multi-agent workflow - Research gathering → Analysis → Writing
* Citation verification - Analyst checks citation counts ≥1
* Quality assurance - Analyst verifies claims are supported by research
* Natural language interaction - Conversational interface with history


## Priority Improvements

### High Priority:
* ORKG Ask integration - Immediate semantic search capability
* Unpaywall integration - OA verification (simple API calls)
* Year-based filtering - Basic query enhancement

### Medium Priority:
* OpenCitations - Citation network analysis
* Multi-factor ranking - Combine multiple signals
* Custom FAISS implementation - Only if ORKG Ask insufficient

### Low Priority:
* OAI-PMH harvesting - Extended coverage
* Custom embedding generation - Redundant if ORKG Ask works

## Other Ideas
* Investigate https://opendoar.ac.uk/ and https://roar.eprints.org/ to
  determine if these are things that can help augment information about the
  availability of research papers.
