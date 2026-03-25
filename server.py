import os
from google.adk.cli.fast_api import get_fast_api_app
from fastapi.staticfiles import StaticFiles

# Determine agents directory
agents_dir = os.environ.get("AGENTS_DIR", os.path.dirname(os.path.abspath(__file__)))

# Get the ADK FastAPI app (no default UI)
app = get_fast_api_app(
    agents_dir=agents_dir,
    web=False,
    allow_origins=["*"],
)

# Mount custom frontend as static files (must be last — catches all unmatched routes)
frontend_dir = os.environ.get(
    "FRONTEND_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend"),
)
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
