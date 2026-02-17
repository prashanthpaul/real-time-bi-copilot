"""
Real-Time BI Copilot — MCP Server
====================================
Main MCP server using the official Python SDK.
Registers tools, resources, and prompts for AI-powered data analytics.

Usage:
    # stdio transport (for VS Code / Claude Desktop)
    python -m mcp_server.server

    # Or via MCP config
    { "command": "python", "args": ["-m", "mcp_server.server"] }
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    Resource,
    Prompt,
    PromptArgument,
    PromptMessage,
    TextContent,
    GetPromptResult,
    ReadResourceResult,
)

# Ensure project root is on sys.path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp_server.config import settings
from mcp_server.utils.db_connector import create_connector
from mcp_server.utils.ai_client import AIClient
from mcp_server.tools.query_database import query_database, TOOL_DEFINITION as QUERY_TOOL
from mcp_server.tools.analyze_data import analyze_data, TOOL_DEFINITION as ANALYZE_TOOL
from mcp_server.tools.generate_insights import generate_insights, TOOL_DEFINITION as INSIGHTS_TOOL
from mcp_server.tools.detect_anomalies import detect_anomalies, TOOL_DEFINITION as ANOMALIES_TOOL
from mcp_server.resources.datasets import list_datasets, get_dataset
from mcp_server.resources.query_history import query_history
from mcp_server.prompts.analytics_workflows import get_prompt, list_prompts

# --- Logging ---
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("bi-copilot-mcp")

# --- Initialize services ---
db_path = settings.resolve_database_path()
db = create_connector()

ai = None
if settings.anthropic_api_key:
    ai = AIClient(api_key=settings.anthropic_api_key, model=settings.claude_model)
    logger.info("AI client initialized")
else:
    logger.warning("ANTHROPIC_API_KEY not set. AI features disabled.")

# --- MCP Server ---
server = Server("bi-copilot")

# Tool definitions
TOOLS = [QUERY_TOOL, ANALYZE_TOOL, INSIGHTS_TOOL, ANOMALIES_TOOL]


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """Return all available MCP tools."""
    return [
        Tool(
            name=t["name"],
            description=t["description"],
            inputSchema=t["inputSchema"],
        )
        for t in TOOLS
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Route tool calls to the appropriate handler."""
    logger.info(f"Tool called: {name} with args: {json.dumps(arguments, default=str)}")

    try:
        if name == "query_database":
            result = await query_database(db=db, ai=ai, **arguments)
        elif name == "analyze_data":
            result = await analyze_data(db=db, **arguments)
        elif name == "generate_insights":
            result = await generate_insights(db=db, ai=ai, **arguments)
        elif name == "detect_anomalies":
            result = await detect_anomalies(db=db, ai=ai, **arguments)
        else:
            result = {"error": f"Unknown tool: {name}"}

        # Record in query history
        if name == "query_database":
            query_history.record(
                query=arguments.get("query", ""),
                query_type=arguments.get("query_type", "auto"),
                result_count=result.get("row_count", 0),
                execution_time_ms=result.get("execution_time_ms", 0),
                success="error" not in result,
                error=result.get("error"),
                generated_sql=result.get("generated_sql"),
            )

        return [TextContent(type="text", text=json.dumps(result, default=str, indent=2))]

    except Exception as e:
        logger.error(f"Tool execution failed: {e}", exc_info=True)
        error_response = {
            "error": str(e),
            "type": type(e).__name__,
            "tool": name,
            "suggestion": "Check logs for details. Ensure the database is initialized.",
        }
        return [TextContent(type="text", text=json.dumps(error_response, indent=2))]


@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    """Return all available MCP resources."""
    return [
        Resource(
            uri="bi-copilot://datasets",
            name="Available Datasets",
            description="List all tables and views available for analysis",
            mimeType="application/json",
        ),
        Resource(
            uri="bi-copilot://query-history",
            name="Query History",
            description="Recent query execution history with performance metrics",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def handle_read_resource(uri: str) -> ReadResourceResult:
    """Handle resource read requests."""
    uri_str = str(uri)
    logger.info(f"Resource read: {uri_str}")

    if uri_str == "bi-copilot://datasets":
        datasets = await list_datasets(db)
        content = json.dumps(datasets, default=str, indent=2)
    elif uri_str.startswith("bi-copilot://datasets/"):
        name = uri_str.split("/")[-1]
        dataset = await get_dataset(name, db)
        content = json.dumps(dataset, default=str, indent=2)
    elif uri_str == "bi-copilot://query-history":
        history = {
            "history": query_history.get_history(),
            "stats": query_history.get_stats(),
        }
        content = json.dumps(history, default=str, indent=2)
    else:
        content = json.dumps({"error": f"Unknown resource: {uri_str}"})

    return ReadResourceResult(
        contents=[TextContent(type="text", text=content)]
    )


@server.list_prompts()
async def handle_list_prompts() -> list[Prompt]:
    """Return all available workflow prompts."""
    prompts = list_prompts()
    return [
        Prompt(
            name=p["name"],
            description=p["description"],
            arguments=[
                PromptArgument(
                    name=a["name"],
                    description=a["description"],
                    required=a.get("required", False),
                )
                for a in p.get("arguments", [])
            ],
        )
        for p in prompts
    ]


@server.get_prompt()
async def handle_get_prompt(name: str, arguments: dict | None = None) -> GetPromptResult:
    """Return a specific workflow prompt with arguments filled in."""
    result = get_prompt(name, arguments)

    if "error" in result:
        return GetPromptResult(
            description=f"Error: {result['error']}",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(type="text", text=result["error"]),
                )
            ],
        )

    return GetPromptResult(
        description=result["description"],
        messages=[
            PromptMessage(
                role=m["role"],
                content=TextContent(type="text", text=m["content"]["text"]),
            )
            for m in result.get("messages", [])
        ],
    )


async def main():
    """Start the MCP server with stdio transport."""
    logger.info("Starting BI Copilot MCP Server...")
    logger.info(f"Database: {db.get_backend_name()} ({db_path})")
    logger.info(f"AI enabled: {ai is not None}")
    logger.info(f"Transport: stdio")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
