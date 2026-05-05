#!/bin/bash
echo "🚀 runKTX Local Start Script (No Docker)"
echo ""

# 1. .env file check
if [ ! -f .env ]; then
    echo "[1/4] .env 파일이 없습니다. 기본 설정을 생성합니다."
    echo "SOLAPI_API_KEY=" > .env
    echo "SOLAPI_API_SECRET=" >> .env
    echo "SOLAPI_SENDER_NUMBER=" >> .env
fi

# 2. Frontend Build check
if [ ! -d "frontend/dist" ]; then
    echo "[2/4] 프론트엔드 빌드 파일이 없습니다. 빌드를 시작합니다..."
    cd frontend
    npm install
    npm run build
    cd ..
else
    echo "[2/4] 프론트엔드 빌드 파일 확인 완료."
fi

# 3. Python Virtual Environment setup
if [ ! -d "backend/venv" ]; then
    echo "[3/4] 파이썬 가상환경을 생성합니다..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
else
    echo "[3/4] 파이썬 가상환경 확인 완료."
fi

# 4. Run Server
echo "[4/4] 서버를 실행합니다..."
source backend/venv/bin/activate
echo "✅ 실행 성공! 브라우저에서 http://localhost:8888 에 접속하세요."

# Open browser based on OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    open http://localhost:8888
else
    xdg-open http://localhost:8888 &> /dev/null || echo "접속 주소: http://localhost:8888"
fi

python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8888
