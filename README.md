<div align="center">
  <div>
    <a href="https://github.com/digitizdat/research-assistant">
      <img src="logo.svg" alt="Research Assistant" width="55px" height="105px">
    </a>
  </div>

  <h1>
    Research Assistant
  </h1>

  <h2>
    An agentic workflow for gathering research for critical decision making
  </h2>

  <div align="center">
    <a href="https://github.com/digitizdat/research-assistant/graphs/commit-activity"><img alt="GitHub commit activity" src="https://img.shields.io/github/commit-activity/m/digitizdat/research-assistant"/></a>
    <a href="https://github.com/digitizdat/research-assistant/issues"><img alt="GitHub open issues" src="https://img.shields.io/github/issues/digitizdat/research-assistant"/></a>
    <a href="https://github.com/digitizdat/research-assistant/pulls"><img alt="GitHub open pull requests" src="https://img.shields.io/github/issues-pr/digitizdat/research-assistant"/></a>
    <a href="https://github.com/digitizdat/research-assistant/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/github/license/digitizdat/research-assistant"/></a>
  </div>
</div>

# Research Assistant

This agentic workflow inspired built on [Strands](https://strandsagents.com/latest/)
implements the following:

### Data Sources:
* research_finder tool - Uses OpenAlex and ORKG Ask APIs to locate relevant
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
* Unpaywall integration - verification of open accessibility for cited papers
* Year-based filtering - Basic query enhancement

### Medium Priority:
* OpenCitations - Citation network analysis
* Multi-factor ranking - Combine multiple signals

### Low Priority:
* OAI-PMH harvesting - Extended coverage

## Other Ideas
* Investigate https://opendoar.ac.uk/ and https://roar.eprints.org/ to
  determine if these are things that can help augment information about the
  availability of research papers.
* Refactor into an independent tool chain for use with MCP
