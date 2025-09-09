from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any

from strands.types.tools import ToolResult, ToolUse

from config_manager import config
from core_tool import core_search
from openalex_tool import openalex_search
from orkg_tool import orkg_search

TOOL_SPEC = {
    "name": "research_finder",
    "description": "AI agent for locating research from the past 20 years related to a given topic. Coordinates OpenAlex and ORKG Ask searches to provide comprehensive research findings with publication details, abstracts, and relevance scores.",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The research topic or keywords to search for",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of research papers to return (configurable via config.yaml)",
                },
                "publication_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Types of publications to include (configurable via config.yaml)",
                },
                "min_year": {
                    "type": "integer",
                    "description": "Minimum publication year (configurable via config.yaml)",
                },
                "enable_openalex": {
                    "type": "boolean",
                    "description": "Override OpenAlex API setting from config.yaml",
                },
                "enable_orkg": {
                    "type": "boolean",
                    "description": "Override ORKG Ask API setting from config.yaml",
                },
                "enable_core": {
                    "type": "boolean",
                    "description": "Override CORE API setting from config.yaml",
                },
            },
            "required": ["topic"],
        }
    },
}


def research_finder(tool_use: ToolUse, **kwargs: Any) -> ToolResult:
    """
    AI agent for locating research from the past 20 years using OpenAlex and ORKG Ask APIs.
    This tool coordinates between OpenAlex and ORKG search tools to provide comprehensive
    research findings with publication details, abstracts, and relevance assessments.
    """
    # Load configuration
    defaults = config.get_defaults()
    behavior_config = config.get_behavior_config()

    tool_use_id = tool_use["toolUseId"]
    topic = tool_use["input"]["topic"]
    max_results = tool_use["input"].get("max_results", defaults.get("max_results", 10))
    publication_types = tool_use["input"].get(
        "publication_types",
        defaults.get("publication_types", ["journal", "conference"]),
    )
    min_year = tool_use["input"].get("min_year", defaults.get("min_year", 2004))

    # Check configuration and input overrides
    enable_openalex = tool_use["input"].get(
        "enable_openalex", config.is_source_enabled("openalex")
    )
    enable_orkg = tool_use["input"].get("enable_orkg", config.is_source_enabled("orkg"))
    enable_core = tool_use["input"].get("enable_core", config.is_source_enabled("core"))
    current_year = datetime.now().year

    # Execute searches and collect raw results
    enabled_sources = []
    if enable_openalex:
        enabled_sources.append("OpenAlex")
    if enable_orkg:
        enabled_sources.append("ORKG Ask")
    if enable_core:
        enabled_sources.append("CORE")

    print(f"🔍 Querying {', '.join(enabled_sources)} for: '{topic}'")
    print(f"📊 Search parameters: max_results={max_results}, min_year={min_year}")

    all_papers = []

    if enable_openalex or enable_orkg or enable_core:
        futures = []
        max_workers = behavior_config.get("max_workers", 3)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            if enable_openalex:
                openalex_tool_use = {
                    "toolUseId": f"{tool_use_id}-openalex",
                    "input": {
                        "topic": topic,
                        "max_results": max_results,
                        "min_year": min_year,
                    },
                }
                futures.append(
                    ("openalex", executor.submit(openalex_search, openalex_tool_use))
                )

            if enable_orkg:
                orkg_tool_use = {
                    "toolUseId": f"{tool_use_id}-orkg",
                    "input": {
                        "topic": topic,
                        "max_results": max_results,
                        "min_year": min_year,
                    },
                }
                futures.append(("orkg", executor.submit(orkg_search, orkg_tool_use)))

            if enable_core:
                core_tool_use = {
                    "toolUseId": f"{tool_use_id}-core",
                    "input": {
                        "topic": topic,
                        "max_results": max_results,
                        "min_year": min_year,
                    },
                }
                futures.append(("core", executor.submit(core_search, core_tool_use)))

            # Collect results and extract paper data
            for source, future in futures:
                try:
                    source_config = config.get_source_config(source)
                    default_timeout = (
                        60 if source == "orkg" else 15 if source == "core" else 40
                    )
                    timeout = source_config.get("timeout", default_timeout)
                    result = future.result(timeout=timeout)
                    if result["status"] == "success":
                        content = result["content"][0]["text"]
                        # Parse papers from tool output
                        papers = parse_papers_from_content(content, source)
                        all_papers.extend(papers)
                except Exception as e:
                    print(f"⚠️ {source} error: {e}")
    else:
        print("⚠️ No research sources enabled")

    # Filter by publication type and year
    filtered_papers = []
    for paper in all_papers:
        # Get publication type from paper data
        pub_type = ""
        if paper.get("journal"):
            pub_type = "journal"
        elif "conference" in paper.get("journal", "").lower():
            pub_type = "conference"

        year = paper.get("year", 0)
        if isinstance(year, str) and year.isdigit():
            year = int(year)
        elif not isinstance(year, int):
            year = 0

        # Check publication type
        type_match = (
            any(pt in pub_type for pt in publication_types) if pub_type else True
        )
        # Check year
        year_match = year >= min_year if year > 0 else True

        if type_match and year_match:
            filtered_papers.append(paper)

    # Limit results
    final_papers = filtered_papers[:max_results]

    # Format response
    response_text = f"🔬 **Research Finder Results for: '{topic}'**\n\n"
    response_text += "📊 **Search Parameters:**\n"
    response_text += f"- Topic: {topic}\n"
    response_text += f"- Time Range: {min_year} - {current_year}\n"
    response_text += f"- Publication Types: {', '.join(publication_types)}\n"
    response_text += f"- Max Results: {max_results}\n\n"

    if final_papers:
        response_text += (
            f"✅ **Found {len(final_papers)} relevant research papers:**\n\n"
        )
        for i, paper in enumerate(final_papers, 1):
            response_text += f"**{i}. {paper.get('title', 'No title')}**\n"
            authors = paper.get("authors", [])
            if isinstance(authors, list):
                authors = ", ".join(authors)
            response_text += f"   👥 Authors: {authors or 'N/A'}\n"
            response_text += f"   📅 Year: {paper.get('year', 'N/A')}\n"
            response_text += f"   📖 Published in: {paper.get('journal', 'N/A')}\n"
            response_text += f"   📈 Citations: {paper.get('citation_count', 0)}\n"
            abstract = paper.get("abstract", "N/A")
            summary = abstract[:200] + "..." if len(abstract) > 200 else abstract
            response_text += f"   📝 Summary: {summary}\n"
            response_text += f"   🔗 DOI: {paper.get('doi', 'N/A')}\n\n"
    else:
        response_text += "❌ No research papers found matching your criteria.\n"
        response_text += (
            "Try broadening your search terms or adjusting the publication types.\n"
        )

    # Add note about enabled sources
    response_text += "\n💡 **Note:** "
    active_sources = []
    if enable_openalex:
        active_sources.append("OpenAlex for bibliographic data")
    if enable_orkg:
        active_sources.append("ORKG Ask for semantic search")
    if enable_core:
        active_sources.append("CORE for open access papers")

    if active_sources:
        response_text += f"This tool uses {', '.join(active_sources)}. "
    else:
        response_text += "No research sources were enabled for this query. "
    response_text += "Citation counts indicate research impact and credibility."

    return {
        "toolUseId": tool_use_id,
        "status": "success",
        "content": [{"text": response_text}],
    }


def parse_papers_from_content(content: str, source: str) -> list:
    """Parse paper data from tool output content."""
    papers = []
    lines = content.split("\n")
    current_paper = {}

    for line in lines:
        line = line.strip()
        if line.startswith("**") and line.endswith("**") and ". " in line:
            # Save previous paper
            if current_paper.get("title"):
                papers.append(current_paper)
            # Start new paper
            title = (
                line.replace("**", "").split(". ", 1)[1]
                if ". " in line
                else line.replace("**", "")
            )
            current_paper = {"title": title, "source": source}
        elif line.startswith("👥 Authors:"):
            authors_str = line.replace("👥 Authors:", "").strip()
            if authors_str != "N/A":
                current_paper["authors"] = [a.strip() for a in authors_str.split(",")]
        elif line.startswith("📅 Year:"):
            year_str = line.replace("📅 Year:", "").strip()
            if year_str != "N/A" and year_str.isdigit():
                current_paper["year"] = int(year_str)
        elif line.startswith("📖 Published in:"):
            journal = line.replace("📖 Published in:", "").strip()
            if journal != "N/A":
                current_paper["journal"] = journal
        elif line.startswith("📈 Citations:"):
            citations_str = line.replace("📈 Citations:", "").strip()
            if citations_str.isdigit():
                current_paper["citation_count"] = int(citations_str)
        elif line.startswith("📝 Summary:"):
            abstract = line.replace("📝 Summary:", "").strip()
            if abstract != "N/A":
                current_paper["abstract"] = abstract
        elif line.startswith("🔗 DOI:"):
            doi = line.replace("🔗 DOI:", "").strip()
            if doi != "N/A":
                current_paper["doi"] = doi

    # Save last paper
    if current_paper.get("title"):
        papers.append(current_paper)

    return papers
