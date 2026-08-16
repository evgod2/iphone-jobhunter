import os
from mcp.server.fastmcp import FastMCP
from jobspy import scrape_jobs
import pandas as pd

# Initialize FastMCP server with proper transport support
mcp = FastMCP("iPhone-JobHunter")

@mcp.tool()
def search_target_jobs(search_term: str, location: str = "Remote", results_wanted: int = 5) -> str:
    """Scrapes live job boards using JobSpy based on search criteria."""
    try:
        jobs_df = scrape_jobs(
            site_name=["indeed", "linkedin", "zip_recruiter"],
            search_term=search_term,
            location=location,
            results_wanted=results_wanted,
            hours_old=72
        )
        if jobs_df.empty:
            return "No recent jobs found matching those parameters."
        
        summary_df = jobs_df[['site', 'title', 'company', 'location', 'job_url']]
        return summary_df.to_json(orient="records")
    except Exception as e:
        return f"Error executing search: {str(e)}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    # Run using Server-Sent Events (SSE) transport which custom apps expect
    mcp.run(transport="sse", host="0.0.0.0", port=port)
