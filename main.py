import os
import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import Optional, List
from pathlib import Path
from contextlib import asynccontextmanager

# Import Gemini service functions
# Make sure gemini_service.py is in the same directory or accessible via PYTHONPATH
from gemini_service import initialize_model, find_local_events_via_search
# Note: We don't directly need generate_content_with_tools for this specific endpoint,
# but initialize_model still sets up the model with tools capability.

# --- Pydantic Models for API Request/Response ---

class EventRequest(BaseModel):
    interest_description: str = Field(..., description="Natural language description of the desired event type.")
    location: str = Field("Blaine, MN", description="The target location (city, state). Defaults to Blaine, MN.")
    # timeframe_days: Optional[int] = Field(14, description="Number of days into the future to search.") # Optional: Could add this later

class EventResponse(BaseModel):
    results_text: str = Field(description="Formatted text summary of found events, or a message indicating none were found.")
    error: Optional[str] = Field(None, description="Error message if the process failed.")

# --- Global variable for the model ---
gemini_model = None

# --- App Lifespan Management (for model initialization) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup (model initialization) and shutdown events."""
    global gemini_model
    print("Application starting up...")
    try:
        # Initialize model using the function from gemini_service
        gemini_model = initialize_model()
        print("Gemini model loaded successfully during startup.")
    except ValueError as e:
        print(f"CRITICAL ERROR during startup: {e}")
        gemini_model = None # Ensure model is None if init fails
    except Exception as e:
        print(f"An unexpected error occurred during model initialization: {e}")
        gemini_model = None
    yield # Application runs here
    # --- Shutdown ---
    print("Application shutting down...")


# --- App Setup ---
app = FastAPI(
    title="Local Event Finder AI",
    description="API to find local events using AI-powered web search.",
    lifespan=lifespan # Use lifespan context manager
)

# --- Static Files & Templates Setup ---
# Assuming your static files (CSS, JS) and templates (HTML) will be in these directories
BASE_DIR = Path(__file__).resolve().parent
try:
    app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
    templates = Jinja2Templates(directory=BASE_DIR / "templates")
    print("Static files and templates directories mounted.")
except RuntimeError as e:
     print(f"Warning: Could not mount static/templates directories (might be missing): {e}")
     # Allow app to run without frontend files for API testing
     templates = None


# --- API Routes ---

# Route to serve the frontend HTML (if templates are available)
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serves the main HTML page for the event finder interface."""
    if templates:
        return templates.TemplateResponse("index.html", {"request": request})
    else:
        # Fallback if templates aren't configured
        return HTMLResponse("<html><body><h1>Local Event Finder API</h1><p>Frontend not available.</p></body></html>")


# Route to handle finding events
@app.post("/find-events", response_model=EventResponse)
async def find_events_api(request_data: EventRequest):
    """
    API endpoint to find local events based on location and interest description.
    Uses Gemini's web search capabilities via the backend service.
    """
    global gemini_model
    if not gemini_model:
        print("Error: /find-events called but Gemini model is not available.")
        # Return error using the Pydantic response model
        return EventResponse(
            results_text="",
            error="AI model is not available. Please check server logs or try again later."
        )

    print(f"Received event search request: Location='{request_data.location}', Interest='{request_data.interest_description}'")

    try:
        # --- Call Gemini Service ---
        # Run the synchronous Gemini call in a separate thread
        # to avoid blocking FastAPI's async event loop
        generated_text_summary = await asyncio.to_thread(
            find_local_events_via_search,
            gemini_model,
            request_data.location,
            request_data.interest_description
            # Optional: Pass timeframe_days if added to request model
            # timeframe_days=request_data.timeframe_days
        )

        # --- Prepare Successful Response ---
        print("Successfully generated event summary.")
        response_data = EventResponse(
            results_text=generated_text_summary
            # error field defaults to None
        )
        return response_data

    except Exception as e:
        print(f"Error processing event search request: {e}")
        # Return error using the Pydantic response model
        return EventResponse(
            results_text="",
            error=f"Failed to find events: {e}"
        )

# --- Basic Error Handling (Optional but good practice) ---
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc: HTTPException):
     print(f"404 Not Found for path: {request.url.path}")
     # You could return JSON or a simple HTML page
     return JSONResponse(
        status_code=404,
        content={"message": f"Error: Resource not found at path {request.url.path}"},
    )

# --- Run Instruction (for local development) ---
# To run this FastAPI application locally:
# 1. Make sure you have uvicorn installed: pip install uvicorn
# 2. Save this code as main.py
# 3. Save the gemini_service.py code in the same directory.
# 4. Create a .env file with your GEMINI_API_KEY.
# 5. Run from your terminal: uvicorn main:app --reload
#    --reload automatically restarts the server when code changes.