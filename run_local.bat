@echo off
setlocal
echo ------------------------------------------
echo runKTX Local Start Script
echo ------------------------------------------

if not exist .env echo [WARNING] .env file not found!
if exist .env echo [1/4] .env file found.

if not exist frontend\dist (
    echo [2/4] Building frontend...
    cd frontend
    call npm install
    call npm run build
    cd ..
) else (
    echo [2/4] Frontend dist found.
)

if not exist backend\venv (
    echo [3/4] Creating venv...
    cd backend
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements.txt
    cd ..
) else (
    echo [3/4] venv found.
)

echo [4/4] Starting server...
if exist backend\venv call backend\venv\Scripts\activate
echo SUCCESS! Visit http://localhost:8888
start http://localhost:8888
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8888
pause