from datetime import datetime
from typing import Any
from strands.types.tools import ToolResult, ToolUse

TOOL_SPEC = {
    "name": "orkg_search",
    "description": "Search ORKG Ask for semantic search on CORE dataset to find relevant scientific papers with enhanced semantic capabilities.",
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


def orkg_search(tool_use: ToolUse, **kwargs: Any) -> ToolResult:
    """Search ORKG Ask API for semantic search on research papers."""
    import requests
    import time

    tool_use_id = tool_use["toolUseId"]
    topic = tool_use["input"]["topic"]
    max_results = tool_use["input"].get("max_results", 10)
    min_year = tool_use["input"].get("min_year", 2004)

    url = "https://api.ask.orkg.org/index/search"
    params = {
        "query": topic,
        "limit": max_results,
        "filter": f"year >= {min_year}" if min_year else None
    }
    params = {k: v for k, v in params.items() if v is not None}

    for attempt in range(3):
        try:
            print(f"🔍 ORKG Ask attempt {attempt + 1}")
            
            headers = {
                "User-Agent": "Research-Assistant/1.0",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            r = requests.get(url, params=params, headers=headers, timeout=15)
            print(f"📡 ORKG Ask status: {r.status_code}")
            
            if r.status_code == 200:
                data = r.json()
                payload = data.get("payload", {})
                items = payload.get("items", [])
                
                print(f"ORKG Ask results count: {len(items)}")
                
                papers = []
                for item in items:
                    year_val = item.get("year")
                    if year_val:
                        try:
                            year_int = int(year_val)
                            if year_int < min_year:
                                continue
                        except (ValueError, TypeError):
                            pass
                    
                    authors = item.get("authors", [])
                    if isinstance(authors, str):
                        authors = [authors]
                    elif not isinstance(authors, list):
                        authors = []
                    
                    journals = item.get("journals", [])
                    journal_name = ""
                    if journals and isinstance(journals, list):
                        journal_name = journals[0]
                    elif isinstance(journals, str):
                        journal_name = journals
                    
                    if item.get("title"):
                        papers.append({
                            "title": item.get("title", ""),
                            "authors": authors,
                            "year": str(year_val) if year_val else "",
                            "journal": journal_name,
                            "doi": item.get("doi", ""),
                            "abstract": item.get("abstract", ""),
                            "citation_count": int(item.get("citation_count", 0)),
                            "relevance_score": 0.8,
                        })

                # Format response
                response_text = f"🧠 **ORKG Ask Results for: '{topic}'**\n\n"
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
                
            elif r.status_code == 422:
                print(f"❌ ORKG validation error: {r.text[:200]}")
                break
            elif r.status_code == 429:
                print(f"⏳ ORKG rate limited, waiting...")
                time.sleep(2 ** attempt)
                continue
            else:
                print(f"❌ ORKG error {r.status_code}: {r.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"⏰ ORKG timeout on attempt {attempt + 1}")
        except requests.exceptions.ConnectionError:
            print(f"🔌 ORKG connection error on attempt {attempt + 1}")
        except Exception as e:
            print(f"⚠️ ORKG unexpected error: {e}")
        
        if attempt < 2:
            time.sleep(1 + attempt)

    return {
        "toolUseId": tool_use_id,
        "status": "success",
        "content": [{"text": f"❌ ORKG search failed for '{topic}' after all attempts"}],
    }