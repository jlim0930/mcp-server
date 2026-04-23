# MCP Documentation Server

A standalone Model Context Protocol (MCP) server that indexes documentation sites and provides a searchable vector store for LLMs.

## Use Cases
- **Internal Knowledge Base**: Index and search your company's internal documentation, wikis, or private GitHub repositories to provide LLMs with private context.
- **API Reference & Documentation**: Quickly crawl and index technical documentation for new libraries or frameworks to assist with coding tasks.
- **Specialized Research**: Create a searchable vector store for niche knowledge sites, medical papers, or legal documents.
- **Offline Access**: Maintain a local, searchable copy of frequently used documentation for use in environments with restricted internet access.

## Features
- **FastMCP**: High-performance MCP implementation.
- **Crawl4AI**: Automatically crawls and converts websites into LLM-friendly Markdown.
- **ChromaDB**: Local, persistent vector database (no API keys required).
- **Supports SSE & stdio**: Compatible with Claude Desktop, Cursor, and other MCP clients.

## Prerequisites
- Docker & Docker Compose (Recommended)
- Python 3.11+ (If running manually)

## Configuration
The server uses the `DOC_SITES` environment variable to define which sites to index. This should be a comma-separated list of URLs. The server will automatically begin crawling and indexing these sites as a background process as soon as it starts up.

You can also use the following optional environment variables:
- `CRAWL_DELAY`: Control the throttling between requests (default is `1.0` seconds) to prevent overloading the target web servers during the recursive crawl.
- `REFRESH_INTERVAL_HOURS`: How often the server should automatically re-crawl the sites to pick up updates (default is `168.0` hours, which is once a week). Set to `0` to disable automatic background refreshing.

Example:
`DOC_SITES=https://docs.example.com,https://api.example.com`
`CRAWL_DELAY=2.0`
`REFRESH_INTERVAL_HOURS=12`

## Setup & Installation

> ⚠️ **Warning**: The MCP server's database size can become quite large, and the initial crawl of the listed documentation sites can take a significant amount of time depending on the volume of content.

### Option 1: Docker (Recommended)
1. Configure your sites in `docker-compose.yml`.
2. Build and run the server:
   ```bash
   docker-compose up -d --build
   ```
   The server will immediately begin indexing your configured sites in the background. It will be available via SSE at `http://localhost:8888/sse`.

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
3. Run the server (auto-indexing will begin immediately):
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

### Gemini CLI
Update your `~/.gemini/settings.json` with the following configuration:

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

### Claude CLI (`claude-code`)
You can add the server using the `claude mcp add` command.

**Using Docker (SSE):**
```bash
claude mcp add mcp-docs-server http://localhost:8888/sse
```

**Using stdio (Manual):**
```bash
claude mcp add mcp-docs-server python /path/to/mcp-server/server.py
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
**Auto-Indexing:** The server automatically runs an indexing job in the background every time it starts up, reading the URLs provided in the `DOC_SITES` environment variable.

Once connected to your client, you can use the following tools:
- `search_docs`: Searches the indexed documentation for relevant snippets based on a query.
- `index_configured_sites`: Manually trigger a re-crawl of the sites defined in `DOC_SITES` (useful if documentation has changed while the server is running).
