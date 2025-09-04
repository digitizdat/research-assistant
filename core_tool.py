from datetime import datetime
from typing import Any
from strands.types.tools import ToolResult, ToolUse

TOOL_SPEC = {
    "name": "core_search",
    "description": "Search CORE aggregation service for open access research papers with full-text content and metadata.",
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


def core_search(tool_use: ToolUse, **kwargs: Any) -> ToolResult:
    """Search CORE aggregation service for open access research papers."""
    import requests
    import time

    tool_use_id = tool_use["toolUseId"]
    topic = tool_use["input"]["topic"]
    max_results = tool_use["input"].get("max_results", 10)
    min_year = tool_use["input"].get("min_year", 2004)

    url = "https://api.core.ac.uk/v3/search/works"
    params = {
        "q": topic,
        "limit": max_results,
        "offset": 0
    }

    for attempt in range(3):
        try:
            print(f"🔍 CORE search attempt {attempt + 1}")
            
            headers = {
                "User-Agent": "Research-Assistant/1.0",
                "Accept": "application/json"
            }
            
            r = requests.get(url, params=params, headers=headers, timeout=15)
            print(f"📡 CORE status: {r.status_code}")
            
            if r.status_code == 200:
                data = r.json()
                results = data.get("results", [])
                
                print(f"CORE results count: {len(results)}")
                
                papers = []
                for item in results:
                    # Extract year from publication date
                    year = None
                    pub_date = item.get("publishedDate") or item.get("depositedDate")
                    if pub_date:
                        try:
                            year = int(pub_date.split("-")[0])
                            if year < min_year:
                                continue
                        except (ValueError, IndexError):
                            pass
                    
                    # Handle authors
                    authors = []
                    author_data = item.get("authors", [])
                    if isinstance(author_data, list):
                        authors = [a.get("name", "") for a in author_data if a.get("name")]
                    
                    # Handle journal/publisher
                    journal = item.get("publisher", "") or item.get("journals", [""])[0] if item.get("journals") else ""
                    
                    if item.get("title"):
                        papers.append({
                            "title": item.get("title", ""),
                            "authors": authors,
                            "year": year,
                            "journal": journal,
                            "doi": item.get("doi", ""),
                            "abstract": item.get("abstract", ""),
                            "citation_count": int(item.get("citationCount", 0)),
                            "relevance_score": 0.7,  # CORE doesn't provide relevance scores
                        })

                # Format response
                response_text = f"🌐 **CORE Results for: '{topic}'**\n\n"
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
                
            elif r.status_code == 429:
                print(f"⏳ CORE rate limited, waiting...")
                time.sleep(2 ** attempt)
                continue
            else:
                print(f"❌ CORE error {r.status_code}: {r.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"⏰ CORE timeout on attempt {attempt + 1}")
        except requests.exceptions.ConnectionError:
            print(f"🔌 CORE connection error on attempt {attempt + 1}")
        except Exception as e:
            print(f"⚠️ CORE unexpected error: {e}")
        
        if attempt < 2:
            time.sleep(1 + attempt)

    return {
        "toolUseId": tool_use_id,
        "status": "success",
        "content": [{"text": f"❌ CORE search failed for '{topic}' after all attempts"}],
    }