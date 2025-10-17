import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.main import app
    import uvicorn
    
    if __name__ == "__main__":
        print("Starting FastAPI server...")
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
except Exception as e:
    print(f"Error starting server: {e}")
    import traceback
    traceback.print_exc()