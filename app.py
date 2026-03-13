import sys
from pathlib import Path
import os
import uvicorn

# Add the current directory to sys.path to ensure 'src' is findable
root_dir = Path(__file__).resolve().parent
sys.path.append(str(root_dir))

# Import the FastAPI app from the main module
try:
    from backend.api.main import app
except ImportError as e:
    print(f"Error importing app: {e}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Directory contents: {os.listdir('.')}")
    raise

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting production server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
