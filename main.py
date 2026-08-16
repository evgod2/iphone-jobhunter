import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from jobspy import scrape_jobs
import pandas as pd

app = FastAPI(title="iPhone JobHunter MCP")

@app.get("/")
@app.get("/health")
def health_check():
    return {"status": "ok", "name": "iPhone-JobHunter"}

@app.post("/")
@app.post("/mcp")
async def handle_mcp(request: Request):
    try:
        body = await request.json()
        method = body.get("method")
        msg_id = body.get("id")

        # Handle MCP handshake / capabilities
        if method == "initialize":
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "iPhone-JobHunter", "version": "1.0.0"}
                }
            })

        # List available tools
        elif method == "tools/list":
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": [
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
                }
            })

        # Execute tool call
        elif method == "tools/call":
            params = body.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name == "search_target_jobs":
                search_term = arguments.get("search_term", "")
                location = arguments.get("location", "Remote")
                results_wanted = int(arguments.get("results_wanted", 5))

                jobs_df = scrape_jobs(
                    site_name=["indeed", "linkedin", "zip_recruiter"],
                    search_term=search_term,
                    location=location,
                    results_wanted=results_wanted,
                    hours_old=72
                )
                if jobs_df.empty:
                    content = "No recent jobs found matching those parameters."
                else:
                    summary_df = jobs_df[['site', 'title', 'company', 'location', 'job_url']]
                    content = summary_df.to_json(orient="records")

                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": content}]
                    }
                })

        return JSONResponse({
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32601, "message": "Method not found"}
        })
    except Exception as e:
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": body.get("id") if 'body' in locals() else None,
            "error": {"code": -32603, "message": str(e)}
        })

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
