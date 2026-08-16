import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from jobspy import scrape_jobs
import pandas as pd

app = FastAPI(title="iPhone JobHunter API")

class SearchRequest(BaseModel):
    search_term: str
    location: str = "Remote"
    results_wanted: int = 5

@app.get("/")
def health_check():
    return {"status": "online", "service": "iPhone JobHunter MCP Bridge"}

@app.post("/search")
def search_jobs_endpoint(payload: SearchRequest):
    """Direct API endpoint for searching jobs via JobSpy."""
    try:
        jobs_df = scrape_jobs(
            site_name=["indeed", "linkedin", "zip_recruiter"],
            search_term=payload.search_term,
            location=payload.location,
            results_wanted=payload.results_wanted,
            hours_old=72
        )
        if jobs_df.empty:
            return {"results": "No recent jobs found matching those parameters."}
        
        summary_df = jobs_df[['site', 'title', 'company', 'location', 'job_url']]
        return {"results": summary_df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
