from datetime import datetime
from typing import Any

from strands.types.tools import ToolResult, ToolUse

TOOL_SPEC = {
    "name": "research_finder",
    "description": "AI agent for locating research from the past 20 years related to a given topic. Searches OpenAlex for bibliographic data and ORKG Ask for semantic search in parallel to provide comprehensive research findings with publication details, abstracts, and relevance scores.",
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
                "publication_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Types of publications to include (e.g., 'journal', 'conference', 'preprint')",
                    "default": ["journal", "conference"],
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


def research_finder(tool_use: ToolUse, **kwargs: Any) -> ToolResult:
    """
    AI agent for locating research from the past 20 years related to a given topic using open-access aggregators.

    This tool queries OpenAlex and ORKG Ask APIs in parallel to provide structured research findings
    including publication details, abstracts, and relevance assessments. ORKG Ask provides semantic search on CORE data.
    """
    from concurrent.futures import ThreadPoolExecutor

    import requests

    tool_use_id = tool_use["toolUseId"]
    topic = tool_use["input"]["topic"]
    max_results = tool_use["input"].get("max_results", 10)
    publication_types = tool_use["input"].get(
        "publication_types", ["journal", "conference"]
    )
    min_year = tool_use["input"].get("min_year", 2004)
    current_year = datetime.now().year

    def query_openalex():
        """Query OpenAlex API"""
        url = "https://api.openalex.org/works"
        params = {
            "search": topic,
            "filter": f"from_publication_date:{min_year}-01-01",
            "sort": "relevance_score:desc",
            "per-page": max_results // 2 if max_results > 1 else 1,
        }
        try:
            r = requests.get(url, params=params, timeout=10)
            print(f"📡 OpenAlex status: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                results = data.get("results", [])
                print(f"OpenAlex raw results count: {len(results)}")
                return [
                    {
                        "title": item.get("title"),
                        "authors": [
                            a.get("author", {}).get("display_name", "")
                            for a in item.get("authorships", [])
                        ],
                        "year": item.get("publication_year"),
                        "journal": item.get("host_venue", {}).get("display_name", ""),
                        "doi": item.get("doi", ""),
                        "abstract": item.get("abstract_inverted_index", {}),
                        "relevance_score": item.get("relevance_score", 0.0),
                        "citation_count": item.get("cited_by_count", 0),
                        "publication_type": item.get("type", ""),
                    }
                    for item in results
                ]
            else:
                print(f"OpenAlex error: {r.text[:200]}")
        except Exception as e:
            print(f"OpenAlex exception: {e}")
        return []

    def query_orkg_ask():
        """Query ORKG Ask API using official specification"""
        import time
        
        # Official ORKG Ask API endpoint from specification
        url = "https://api.ask.orkg.org/index/search"
        
        # Parameters according to API spec
        params = {
            "query": topic,
            "limit": max_results // 2 if max_results > 1 else 1,
            "filter": f"year >= {min_year}" if min_year else None
        }
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        for attempt in range(3):  # 3 retry attempts
            try:
                print(f"🔍 ORKG Ask attempt {attempt + 1}")
                
                # Headers according to API best practices
                headers = {
                    "User-Agent": "Research-Assistant/1.0",
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }
                
                r = requests.get(url, params=params, headers=headers, timeout=15)
                print(f"📡 ORKG Ask status: {r.status_code}")
                
                if r.status_code == 200:
                    try:
                        data = r.json()
                        
                        # Parse according to QdrantPagedDocumentsResponse schema
                        payload = data.get("payload", {})
                        items = payload.get("items", [])
                        
                        print(f"ORKG Ask raw results count: {len(items)}")
                        
                        if items:
                            results = []
                            for item in items:
                                # Extract fields according to QdrantDocument schema
                                year_val = item.get("year")
                                if year_val:
                                    try:
                                        year_int = int(year_val)
                                        if year_int < min_year:
                                            continue
                                    except (ValueError, TypeError):
                                        pass
                                
                                # Handle authors field (can be array or string)
                                authors = item.get("authors", [])
                                if isinstance(authors, str):
                                    authors = [authors]
                                elif not isinstance(authors, list):
                                    authors = []
                                
                                # Handle journals field (array in spec)
                                journals = item.get("journals", [])
                                journal_name = ""
                                if journals and isinstance(journals, list):
                                    journal_name = journals[0]
                                elif isinstance(journals, str):
                                    journal_name = journals
                                
                                result = {
                                    "title": item.get("title", ""),
                                    "authors": authors,
                                    "year": str(year_val) if year_val else "",
                                    "journal": journal_name,
                                    "doi": item.get("doi", ""),
                                    "abstract": item.get("abstract", ""),
                                    "relevance_score": 0.8,  # ORKG doesn't provide scores in search
                                    "citation_count": int(item.get("citation_count", 0)),
                                    "publication_type": item.get("document_type", "journal"),
                                    "source": "ORKG",
                                }
                                
                                if result["title"]:  # Only include if has title
                                    results.append(result)
                            
                            return results
                        
                    except (ValueError, KeyError) as e:
                        print(f"❌ ORKG JSON parsing error: {e}")
                        print(f"📄 Response preview: {r.text[:200]}")
                
                elif r.status_code == 422:
                    print(f"❌ ORKG validation error: {r.text[:200]}")
                    break  # Don't retry validation errors
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
            
            if attempt < 2:  # Don't sleep on last attempt
                time.sleep(1 + attempt)  # Progressive delay
        
        print("❌ ORKG Ask failed after all attempts")
        return []

    # Execute API calls in parallel with diagnostics and timeout
    print(f"🔍 Querying OpenAlex and ORKG Ask for: '{topic}'")
    print(f"📊 Search parameters: max_results={max_results}, min_year={min_year}")

    with ThreadPoolExecutor(max_workers=2) as executor:
        openalex_future = executor.submit(query_openalex)
        orkg_future = executor.submit(query_orkg_ask)

        try:
            openalex_results = openalex_future.result(timeout=30)
            orkg_results = orkg_future.result(timeout=50)
        except Exception as e:
            print(f"⚠️ Timeout or error occurred: {e}")
            # Get partial results if available
            try:
                openalex_results = (
                    openalex_future.result(timeout=0.1)
                    if not openalex_future.done()
                    else openalex_future.result()
                )
            except:
                openalex_results = []
            try:
                orkg_results = (
                    orkg_future.result(timeout=0.1)
                    if not orkg_future.done()
                    else orkg_future.result()
                )
            except:
                orkg_results = []

    # Diagnostic output
    print(f"\n📊 OpenAlex returned {len(openalex_results)} results")
    for i, result in enumerate(openalex_results[:3], 1):
        print(
            f"  {i}. {result.get('title', 'No title')[:60]}... (Citations: {result.get('citation_count', 0)})"
        )

    print(f"\n🧠 ORKG Ask returned {len(orkg_results)} results")
    for i, result in enumerate(orkg_results[:3], 1):
        print(
            f"  {i}. {result.get('title', 'No title')[:60]}... (Score: {result.get('relevance_score', 0):.2f})"
        )

    # Process and merge results
    research_results = []

    # Process OpenAlex results (convert inverted index abstracts)
    for r in openalex_results:
        if isinstance(r["abstract"], dict):
            idx = r["abstract"]
            if idx:
                words = [None] * (max([max(v) for v in idx.values()]) + 1)
                for word, positions in idx.items():
                    for pos in positions:
                        words[pos] = word
                r["abstract"] = " ".join([w for w in words if w])
            else:
                r["abstract"] = ""
        research_results.append(r)

    research_results.extend(orkg_results)
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
    response_text += "📊 **Search Parameters:**\n"
    response_text += f"- Topic: {topic}\n"
    response_text += f"- Time Range: {min_year} - {current_year}\n"
    response_text += f"- Publication Types: {', '.join(publication_types)}\n"
    response_text += f"- Max Results: {max_results}\n\n"

    if not research_results:
        response_text += "❌ No research papers found matching your criteria.\n"
        response_text += (
            "Try broadening your search terms or adjusting the publication types."
        )
    else:
        response_text += (
            f"✅ **Found {len(research_results)} relevant research papers:**\n\n"
        )
        for i, paper in enumerate(research_results, 1):
            response_text += f"**{i}. {paper.get('title', 'No title')}**\n"
            authors = paper.get("authors")
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

    response_text += "\n💡 **Note:** This tool uses OpenAlex for bibliographic data and ORKG Ask for semantic search. "
    response_text += (
        "ORKG Ask is built on CORE dataset with enhanced semantic capabilities. "
    )
    response_text += "Citation counts indicate research impact and credibility."

    return {
        "toolUseId": tool_use_id,
        "status": "success",
        "content": [{"text": response_text}],
    }
