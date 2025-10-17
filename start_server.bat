@echo off
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt

echo Starting the API server...
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause