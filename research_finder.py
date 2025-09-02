from typing import Any
from strands.types.tools import ToolUse, ToolResult
import json
from datetime import datetime

TOOL_SPEC = {
    "name": "research_finder",
    "description": "AI agent for locating research from the past 20 years related to a given topic. Searches academic databases and provides comprehensive research findings with publication details, abstracts, and relevance scores.",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The research topic or keywords to search for"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of research papers to return (default: 10)",
                    "default": 10
                },
                "publication_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Types of publications to include (e.g., 'journal', 'conference', 'preprint')",
                    "default": ["journal", "conference"]
                },
                "min_year": {
                    "type": "integer",
                    "description": "Minimum publication year (default: 20 years ago)",
                    "default": 2004
                }
            },
            "required": ["topic"]
        }
    }
}

def research_finder(tool_use: ToolUse, **kwargs: Any) -> ToolResult:
    """
    AI agent for locating research from the past 20 years related to a given topic using open-access aggregators.

    This tool queries OpenAlex and CORE APIs to provide structured research findings
    including publication details, abstracts, and relevance assessments.
    """
    import requests
    tool_use_id = tool_use["toolUseId"]
    topic = tool_use["input"]["topic"]
    max_results = tool_use["input"].get("max_results", 10)
    publication_types = tool_use["input"].get("publication_types", ["journal", "conference"])
    min_year = tool_use["input"].get("min_year", 2004)
    current_year = datetime.now().year

    # Helper: Map publication_types to OpenAlex types
    openalex_type_map = {
        "journal": "journal-article",
        "conference": "proceedings-article",
        "preprint": "posted-content"
    }
    openalex_types = [openalex_type_map.get(pt, pt) for pt in publication_types]

    # Query OpenAlex
    openalex_url = "https://api.openalex.org/works"
    openalex_params = {
        "filter": f"title.search:{topic},publication_year:>={min_year},type:{{{','.join(openalex_types)}}}",
        "sort": "relevance_score:desc",
        "per-page": max_results // 2 if max_results > 1 else 1
    }
    openalex_results = []
    try:
        r = requests.get(openalex_url, params=openalex_params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            for item in data.get("results", []):
                openalex_results.append({
                    "title": item.get("title"),
                    "authors": [a.get("author", {}).get("display_name", "") for a in item.get("authorships", [])],
                    "year": item.get("publication_year"),
                    "journal": item.get("host_venue", {}).get("display_name", ""),
                    "doi": item.get("doi", ""),
                    "abstract": item.get("abstract_inverted_index", {}),
                    "relevance_score": item.get("relevance_score", 0.0),
                    "citation_count": item.get("cited_by_count", 0),
                    "publication_type": item.get("type", "")
                })
    except Exception as e:
        openalex_results = []

    # Query CORE
    # Note: CORE API v3 requires an API key for full access. We'll use the public search endpoint for demonstration.
    core_url = "https://core.ac.uk:443/api-v2/search/"
    core_params = {
        "q": topic,
        "page": 1,
        "pageSize": max_results // 2 if max_results > 1 else 1,
        "yearFrom": min_year,
        "yearTo": current_year
    }
    # You can add 'apiKey': 'YOUR_API_KEY' to core_params if you have one
    core_results = []
    try:
        r = requests.get(core_url, params=core_params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            for item in data.get("data", []):
                core_results.append({
                    "title": item.get("title"),
                    "authors": item.get("authors", []),
                    "year": item.get("publishedDate", "")[:4],
                    "journal": item.get("publisher", ""),
                    "doi": item.get("doi", ""),
                    "abstract": item.get("description", ""),
                    "relevance_score": 0.8,  # CORE does not provide, so set a default
                    "citation_count": item.get("citations", 0),
                    "publication_type": item.get("type", "")
                })
    except Exception as e:
        core_results = []

    # Merge and format results
    research_results = []
    for r in openalex_results:
        # OpenAlex abstracts are inverted index, convert to string
        if isinstance(r["abstract"], dict):
            # Reconstruct abstract from inverted index
            idx = r["abstract"]
            words = [None] * (max([max(v) for v in idx.values()]) + 1) if idx else []
            for word, positions in idx.items():
                for pos in positions:
                    words[pos] = word
            r["abstract"] = " ".join([w for w in words if w])
        research_results.append(r)
    research_results.extend(core_results)
    # Filter by publication type and year (in case APIs returned extra)
    filtered_results = []
    for result in research_results:
        pub_type = result.get("publication_type", "").lower()
        year = int(result.get("year", 0)) if result.get("year") else 0
        if any(pt in pub_type for pt in publication_types) and year >= min_year:
            filtered_results.append(result)
    # Limit results
    research_results = filtered_results[:max_results]

    # Format the response
    response_text = f"🔬 **Research Finder Results for: '{topic}'**\n\n"
    response_text += f"📊 **Search Parameters:**\n"
    response_text += f"- Topic: {topic}\n"
    response_text += f"- Time Range: {min_year} - {current_year}\n"
    response_text += f"- Publication Types: {', '.join(publication_types)}\n"
    response_text += f"- Max Results: {max_results}\n\n"

    if not research_results:
        response_text += "❌ No research papers found matching your criteria.\n"
        response_text += "Try broadening your search terms or adjusting the publication types."
    else:
        response_text += f"✅ **Found {len(research_results)} relevant research papers:**\n\n"
        for i, paper in enumerate(research_results, 1):
            response_text += f"**{i}. {paper.get('title', 'No title')}**\n"
            authors = paper.get('authors')
            if isinstance(authors, list):
                authors = ', '.join(authors)
            response_text += f"   👥 Authors: {authors or 'N/A'}\n"
            response_text += f"   📅 Year: {paper.get('year', 'N/A')}\n"
            response_text += f"   📖 Published in: {paper.get('journal', 'N/A')}\n"
            response_text += f"   📈 Citations: {paper.get('citation_count', 0)}\n"
            abstract = paper.get('abstract', 'N/A')
            summary = abstract[:200] + '...' if len(abstract) > 200 else abstract
            response_text += f"   📝 Summary: {summary}\n"
            response_text += f"   🔗 DOI: {paper.get('doi', 'N/A')}\n\n"

    response_text += "\n💡 **Note:** This tool uses open-access APIs (OpenAlex, CORE) for research discovery. "
    response_text += "Citation counts indicate research impact and credibility. "
    response_text += "Some results may be limited by API access or rate limits."

    return {
        "toolUseId": tool_use_id,
        "status": "success",
        "content": [{"text": response_text}]
    }