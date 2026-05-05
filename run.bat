@echo off
setlocal
echo ------------------------------------------
echo runKTX Docker Start Script
echo ------------------------------------------

if not exist .env echo [WARNING] .env file not found!

docker -v >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed or running!
    pause
    exit /b 1
)

echo [2/3] Building and starting containers...
docker-compose up -d --build

if %errorlevel% equ 0 (
    echo SUCCESS! Visit http://localhost:8888
    start http://localhost:8888
) else (
    echo FAILED! Check Docker Desktop.
)

pause