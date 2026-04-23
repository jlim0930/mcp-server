# MCP Documentation Server

A standalone Model Context Protocol (MCP) server that indexes documentation sites and provides a searchable vector store for LLMs.

## Features
- **FastMCP**: High-performance MCP implementation.
- **Crawl4AI**: Automatically crawls and converts websites into LLM-friendly Markdown.
- **ChromaDB**: Local, persistent vector database (no API keys required).
- **Supports SSE & stdio**: Compatible with Claude Desktop, Cursor, and other MCP clients.

## Prerequisites
- Docker & Docker Compose (Recommended)
- Python 3.11+ (If running manually)

## Configuration
The server uses the `DOC_SITES` environment variable to define which sites to index. This should be a comma-separated list of URLs.

Example:
`DOC_SITES=https://docs.example.com,https://api.example.com`

## Setup & Installation

### Option 1: Docker (Recommended)
1. Configure your sites in `docker-compose.yml`.
2. Build and run the server:
   ```bash
   docker-compose up -d --build
   ```
   The server will be available via SSE at `http://localhost:8888/sse`.

3. **View logs:**
   To monitor the server and see indexing progress:
   ```bash
   docker-compose logs -f
   ```

4. **Shut down:**
   To stop and remove the container:
   ```bash
   docker-compose down
   ```

### Option 2: Manual Installation
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   playwright install-deps chromium
   ```
2. Set the environment variable:
   ```bash
   export DOC_SITES=https://docs.example.com
   ```
3. Run the server:
   - For `stdio` (default): `python server.py`
   - For `sse`: `python server.py sse`

## Bootstrapping to LLMs

### Claude Desktop
Add the following to your `claude_desktop_config.json`:

**Using Docker (SSE):**
```json
{
  "mcpServers": {
    "mcp-docs-server": {
      "url": "http://localhost:8888/sse"
    }
  }
}
```

**Using stdio (Manual):**
```json
{
  "mcpServers": {
    "mcp-docs-server": {
      "command": "python",
      "args": ["/path/to/mcp-server/server.py"],
      "env": {
        "DOC_SITES": "https://docs.example.com"
      }
    }
  }
}
```

### Cursor
1. Go to **Settings > Cursor Settings > Features > MCP Servers**.
2. Click **+ Add New MCP Server**.
3. **Name**: `mcp-docs-server`
4. **Type**: `sse`
5. **URL**: `http://localhost:8888/sse`

### Other MCP Clients (e.g., Windsurf, etc.)
Most clients support either `stdio` (command-based) or `sse` (URL-based). Follow the client's documentation for adding an MCP server using one of these methods.

## Using the Server
Once connected, you can use the following tools:
- `index_configured_sites`: Crawls the sites defined in `DOC_SITES` and stores them in the vector database.
- `search_docs`: Searches the indexed documentation for relevant snippets based on a query.
