#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# WSL 에서 run-express 를 포그라운드로 실행한다. (개발 / 동작 확인용)
# 상시 운영은 scripts/wsl_service_install.sh 로 systemd 서비스를 쓰세요.
#   사용법: ./run_wsl.sh [포트]        (기본 8888)
# ---------------------------------------------------------------------------
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"
PORT="${1:-8888}"

log()  { printf '\033[1;36m[run]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31m[error]\033[0m %s\n' "$*" >&2; exit 1; }

grep -qi microsoft /proc/version 2>/dev/null \
  || die "이 스크립트는 WSL 안에서 실행해야 합니다. (Windows 는 run_local.bat)"

# 1) 사전 조건
[ -x backend/venv/bin/python ] \
  || die "backend/venv 가 없습니다. 먼저 'bash scripts/wsl_bootstrap.sh' 를 실행하세요."

if [ ! -f .env ]; then
  warn ".env 가 없어 .env.example 을 복사합니다."
  cp .env.example .env
fi

if [ ! -d frontend/dist ]; then
  log "프론트엔드 빌드 결과가 없어 지금 빌드합니다..."
  (cd frontend && npm install --no-audit --no-fund && npm run build)
fi

# 2) systemd 서비스와 포트 충돌 방지
if command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet run-express 2>/dev/null; then
  warn "run-express systemd 서비스가 이미 실행 중입니다. (포트 충돌 가능)"
  warn "중지하려면: sudo systemctl stop run-express"
fi

# 3) 실행
log "http://localhost:${PORT} 에서 접속할 수 있습니다. (종료: Ctrl+C)"
if command -v wslview >/dev/null 2>&1; then
  wslview "http://localhost:${PORT}" >/dev/null 2>&1 &
elif command -v explorer.exe >/dev/null 2>&1; then
  explorer.exe "http://localhost:${PORT}" >/dev/null 2>&1 || true
fi

export TZ=Asia/Seoul PYTHONUNBUFFERED=1
exec backend/venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port "$PORT"
