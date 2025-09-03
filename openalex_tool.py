from datetime import datetime
from typing import Any
from strands.types.tools import ToolResult, ToolUse

TOOL_SPEC = {
    "name": "openalex_search",
    "description": "Search OpenAlex for bibliographic data and citation information on scientific papers from the past 20 years.",
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
                    "description": "Maximum number of research papers to return (default: 10)",
                    "default": 10,
                },
                "min_year": {
                    "type": "integer",
                    "description": "Minimum publication year (default: 20 years ago)",
                    "default": 2004,
                },
            },
            "required": ["topic"],
        }
    },
}


def openalex_search(tool_use: ToolUse, **kwargs: Any) -> ToolResult:
    """Search OpenAlex for bibliographic data and citation information."""
    import requests

    tool_use_id = tool_use["toolUseId"]
    topic = tool_use["input"]["topic"]
    max_results = tool_use["input"].get("max_results", 10)
    min_year = tool_use["input"].get("min_year", 2004)

    url = "https://api.openalex.org/works"
    params = {
        "search": topic,
        "filter": f"from_publication_date:{min_year}-01-01",
        "sort": "relevance_score:desc",
        "per-page": max_results,
    }

    try:
        r = requests.get(url, params=params, timeout=30)
        print(f"📡 OpenAlex status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            results = data.get("results", [])
            print(f"OpenAlex results count: {len(results)}")
            
            papers = []
            for item in results:
                # Convert inverted index abstract
                abstract_idx = item.get("abstract_inverted_index", {})
                abstract = ""
                if abstract_idx:
                    words = [None] * (max([max(v) for v in abstract_idx.values()]) + 1)
                    for word, positions in abstract_idx.items():
                        for pos in positions:
                            words[pos] = word
                    abstract = " ".join([w for w in words if w])

                papers.append({
                    "title": item.get("title", ""),
                    "authors": [
                        a.get("author", {}).get("display_name", "")
                        for a in item.get("authorships", [])
                    ],
                    "year": item.get("publication_year"),
                    "journal": item.get("host_venue", {}).get("display_name", ""),
                    "doi": item.get("doi", ""),
                    "abstract": abstract,
                    "citation_count": item.get("cited_by_count", 0),
                    "relevance_score": item.get("relevance_score", 0.0),
                })

            # Format response
            response_text = f"🔬 **OpenAlex Results for: '{topic}'**\n\n"
            response_text += f"📊 Found {len(papers)} papers from {min_year} onwards\n\n"

            if papers:
                for i, paper in enumerate(papers, 1):
                    response_text += f"**{i}. {paper['title']}**\n"
                    authors = ", ".join(paper["authors"])
                    response_text += f"   👥 Authors: {authors or 'N/A'}\n"
                    response_text += f"   📅 Year: {paper['year'] or 'N/A'}\n"
                    response_text += f"   📖 Journal: {paper['journal'] or 'N/A'}\n"
                    response_text += f"   📈 Citations: {paper['citation_count']}\n"
                    abstract = paper["abstract"][:200] + "..." if len(paper["abstract"]) > 200 else paper["abstract"]
                    response_text += f"   📝 Abstract: {abstract or 'N/A'}\n"
                    response_text += f"   🔗 DOI: {paper['doi'] or 'N/A'}\n\n"
            else:
                response_text += "❌ No papers found matching your criteria.\n"

            return {
                "toolUseId": tool_use_id,
                "status": "success",
                "content": [{"text": response_text}],
            }
        else:
            print(f"OpenAlex error: {r.text[:200]}")
    except Exception as e:
        print(f"OpenAlex exception: {e}")

    return {
        "toolUseId": tool_use_id,
        "status": "success",
        "content": [{"text": f"❌ OpenAlex search failed for '{topic}'"}],
    }