# PowerShell script to start the API server
Write-Host "Activating virtual environment..." -ForegroundColor Green
& ".\venv\Scripts\Activate.ps1"

Write-Host "Installing dependencies..." -ForegroundColor Green
pip install -r requirements.txt

Write-Host "Starting the API server..." -ForegroundColor Green
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000