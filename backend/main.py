from fastapi import FastAPI
from services.api import router

# --- FastAPI Application Setup ---
app = FastAPI(
    title="LLM Credit Card Analysis Backend",
    description="FastAPI service for managing chat sessions, file uploads, and document analysis.",
    version="1.0.0"
)

# Include the router containing all API endpoints
app.include_router(
    router,
    prefix="/api/v1", # All endpoints will start with /api/v1
    tags=["Analysis Service"]
)

@app.get("/")
def read_root():
    """Root endpoint to check API status."""
    return {"message": "Credit Card Analysis Backend is running! (FastAPI)"}

# To run this server locally, you would execute:
# uvicorn backend.main:app --reload