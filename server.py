import os
import asyncio
from typing import List
from urllib.parse import urldefrag
from collections import deque
from fastmcp import FastMCP
from fastmcp.server.lifespan import lifespan
from crawl4ai import AsyncWebCrawler
import chromadb

# 1. Setup ChromaDB (Local & Persistent)
# By default, ChromaDB uses 'all-MiniLM-L6-v2' embeddings locally.
# No API keys are required for this setup.
DB_PATH = "./chroma_db"
client = chromadb.PersistentClient(path=DB_PATH)
collection = client.get_or_create_collection(name="documentation_store")

def get_target_sites() -> List[str]:
    """Helper to parse DOC_SITES from environment variables."""
    sites_str = os.getenv("DOC_SITES", "")
    if not sites_str:
        return []
    return [s.strip() for s in sites_str.split(",") if s.strip()]

async def run_indexing():
    """
    Core logic for crawling and indexing sites.
    Shared by the tool and the automatic startup process.
    """
    seed_sites = get_target_sites()
    if not seed_sites:
        print("Indexing skipped: No sites found in DOC_SITES.")
        return "Error: No sites found in DOC_SITES environment variable."
        
    try:
        crawl_delay = float(os.getenv("CRAWL_DELAY", "1.0"))
    except ValueError:
        crawl_delay = 1.0

    results_summary = []
    visited = set()
    queue = deque(seed_sites)

    async with AsyncWebCrawler() as crawler:
        while queue:
            current_url = queue.popleft()
            
            # Strip fragment (e.g., #section) to avoid duplicate crawling
            current_url, _ = urldefrag(current_url)
            
            if current_url in visited:
                continue
                
            visited.add(current_url)
            print(f"Indexing: {current_url}")
            
            # arun() fetches and converts to LLM-friendly Markdown automatically
            result = await crawler.arun(url=current_url)

            if result.success:
                # Upsert into vector store
                # We use the URL as the ID to avoid duplicate entries
                collection.upsert(
                    documents=[result.markdown],
                    metadatas=[{"source": current_url}],
                    ids=[current_url]
                )
                results_summary.append(f"✅ Indexed: {current_url}")
                
                # Recursively add internal links under the configured seed sites
                internal_links = result.links.get("internal", [])
                for link_obj in internal_links:
                    href = link_obj.get("href")
                    if href:
                        href_clean, _ = urldefrag(href)
                        # Ensure the link is within one of the root seed sites
                        if any(href_clean.startswith(seed) for seed in seed_sites):
                            if href_clean not in visited and href_clean not in queue:
                                queue.append(href_clean)
            else:
                results_summary.append(f"❌ Failed: {current_url} ({result.error_message})")
                
            # Throttle requests to be polite to the target server and local CPU
            if queue:
                await asyncio.sleep(crawl_delay)

    summary = "\n".join(results_summary)
    print(f"Indexing complete:\n{summary}")
    return summary

# 2. Define Lifespan for Automatic Indexing on Startup
# Note: FastMCP 3.0+ uses this pattern for lifecycle events.

async def periodic_indexing():
    """Runs the indexing job periodically in the background."""
    try:
        refresh_hours = float(os.getenv("REFRESH_INTERVAL_HOURS", "168.0"))
    except ValueError:
        refresh_hours = 168.0
        
    if refresh_hours <= 0:
        print("Periodic indexing is disabled (REFRESH_INTERVAL_HOURS <= 0).")
        return

    sleep_seconds = refresh_hours * 3600
    while True:
        await asyncio.sleep(sleep_seconds)
        print(f"Starting scheduled periodic indexing (every {refresh_hours} hours)...")
        await run_indexing()

@lifespan
async def app_lifespan(server: FastMCP):
    """
    Automatically trigger indexing when the server starts,
    and schedule periodic background updates.
    """
    sites = get_target_sites()
    if sites:
        print(f"Auto-indexing started for: {', '.join(sites)}")
        # Run initial indexing in background to not block server startup
        asyncio.create_task(run_indexing())
        
        # Start the periodic background refresh
        asyncio.create_task(periodic_indexing())
    
    yield  # Server runs here

# 3. Initialize FastMCP
mcp = FastMCP("RemoteDocIndexer", lifespan=app_lifespan)

@mcp.tool()
async def index_configured_sites():
    """
    Crawls the sites defined in the DOC_SITES env var and
    stores them in the local vector database.
    """
    return await run_indexing()

@mcp.tool()
async def search_docs(query: str):
    """
    Searches the local vector store for documentation snippets
    relevant to the user's query.
    """
    # Query the top 3 most relevant sections
    results = collection.query(
        query_texts=[query],
        n_results=3
    )

    if not results["documents"] or not results["documents"][0]:
        return "No relevant documentation found. Try indexing the sites first."

    # Format the output for the LLM
    output = "Found the following relevant information:\n"
    for doc, metadata in zip(results["documents"][0], results["metadatas"][0]):
        output += f"\n--- Source: {metadata['source']} ---\n{doc[:2000]}...\n"

    return output

if __name__ == "__main__":
    import sys
    # If "sse" is passed as an argument, run with SSE transport
    if len(sys.argv) > 1 and sys.argv[1] == "sse":
        mcp.run(transport="sse", host="0.0.0.0", port=8000)
    else:
        # Default to stdio for "docker run" compatibility
        mcp.run()
