@echo off
REM Startup script for FastAPI backend server (Windows)

echo Starting Pramana AI FastAPI Backend Server...
echo API will be available at http://localhost:8000
echo API documentation at http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn src.api.server:app --reload --port 8000
