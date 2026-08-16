import os
from fastapi import FastAPI
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from jobspy import scrape_jobs
import pandas as pd

# Initialize standard MCP server
app_mcp = Server("iPhone-JobHunter")

@app_mcp.list_tools()
async def list_tools():
    return [
        {
            "name": "search_target_jobs",
            "description": "Scrapes live job boards using JobSpy based on search criteria.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "search_term": {"type": "string", "description": "Job title or keywords"},
                    "location": {"type": "string", "description": "Location or Remote"},
                    "results_wanted": {"type": "integer", "description": "Number of results"}
                },
                "required": ["search_term"]
            }
        }
    ]

@app_mcp.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "search_target_jobs":
        search_term = arguments.get("search_term", "")
        location = arguments.get("location", "Remote")
        results_wanted = int(arguments.get("results_wanted", 5))
        
        try:
            jobs_df = scrape_jobs(
                site_name=["indeed", "linkedin", "zip_recruiter"],
                search_term=search_term,
                location=location,
                results_wanted=results_wanted,
                hours_old=72
            )
            if jobs_df.empty:
                return [{"type": "text", "text": "No recent jobs found matching those parameters."}]
            
            summary_df = jobs_df[['site', 'title', 'company', 'location', 'job_url']]
            return [{"type": "text", "text": summary_df.to_json(orient="records")}]
        except Exception as e:
            return [{"type": "text", "text": f"Error executing search: {str(e)}"}]
    raise ValueError(f"Unknown tool: {name}")

# Set up Starlette routing for SSE Transport
sse = SseServerTransport("/messages")

async def handle_sse(request):
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await app_mcp.run(
            streams[0], streams[1], app_mcp.create_initialization_options()
        )

starlette_app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse),
        Mount("/messages", app=sse.handle_post_message),
    ]
)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(starlette_app, host="0.0.0.0", port=port)
