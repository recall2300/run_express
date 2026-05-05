#!/bin/bash
echo "🚀 runKTX Start Script (Unix/Mac)"
echo ""

# 1. .env file check
if [ ! -f .env ]; then
    echo "[1/3] .env 파일이 없습니다. 기본 설정을 생성합니다."
    echo "SOLAPI_API_KEY=" > .env
    echo "SOLAPI_API_SECRET=" >> .env
    echo "SOLAPI_SENDER_NUMBER=" >> .env
else
    echo "[1/3] .env 파일 확인 완료."
fi

# 2. Docker check
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker가 설치되어 있지 않습니다!"
    echo "Docker를 설치하고 다시 실행해 주세요."
    exit 1
fi
echo "[2/3] Docker 확인 완료."

# 3. Docker Compose run
echo "[3/3] 컨테이너를 빌드하고 실행합니다..."
docker-compose up -d --build

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 실행 성공! 브라우저를 엽니다..."
    # OS별 브라우저 열기 명령어
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open http://localhost:8888
    else
        xdg-open http://localhost:8888 &> /dev/null || echo "접속 주소: http://localhost:8888"
    fi
else
    echo ""
    echo "❌ 실행 실패! Docker가 실행 중인지 확인해 주세요."
fi

echo ""
echo "이 창을 닫아도 프로그램은 백그라운드에서 계속 실행됩니다."
