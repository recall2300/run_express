#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# WSL(Ubuntu) 초기 셋업 스크립트
#   - 시스템 패키지 / 타임존(Asia/Seoul) / systemd 활성화 확인
#   - Node.js 22 LTS 설치 (Vite 8 요구사항: Node 20.19+ 또는 22.12+)
#   - Python 가상환경 생성 + 백엔드 의존성 설치
#   - 프론트엔드 빌드
# 사용법:  bash scripts/wsl_bootstrap.sh
# ---------------------------------------------------------------------------
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

log()  { printf '\n\033[1;36m[bootstrap]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*"; }
die()  { printf '\n\033[1;31m[error]\033[0m %s\n' "$*" >&2; exit 1; }

# --- 0. 실행 환경 확인 -------------------------------------------------------
grep -qi microsoft /proc/version 2>/dev/null \
  || die "이 스크립트는 WSL 안에서 실행해야 합니다."
[ -f /etc/debian_version ] \
  || die "Ubuntu/Debian 계열 배포판이 필요합니다. (현재 배포판 미지원)"

case "$PROJECT_DIR" in
  /mnt/*)
    warn "프로젝트가 Windows 드라이브(/mnt/...)에 있습니다."
    warn "빌드 속도와 파일 권한을 위해 'bash scripts/wsl_migrate.sh' 로 WSL 내부로 옮기는 것을 권장합니다."
    ;;
esac

log "프로젝트 경로: $PROJECT_DIR"

# --- 1. 시스템 패키지 --------------------------------------------------------
log "[1/6] APT 패키지를 설치합니다. (sudo 비밀번호가 필요할 수 있습니다)"
sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
  python3 python3-venv python3-pip \
  git curl ca-certificates build-essential tzdata rsync

# --- 2. 타임존 (예매 시각 계산에 필수) ---------------------------------------
log "[2/6] 타임존을 Asia/Seoul 로 설정합니다."
sudo ln -snf /usr/share/zoneinfo/Asia/Seoul /etc/localtime
echo "Asia/Seoul" | sudo tee /etc/timezone >/dev/null
sudo dpkg-reconfigure -f noninteractive tzdata >/dev/null 2>&1 || true
log "현재 시각: $(date '+%Y-%m-%d %H:%M:%S %Z')"

# --- 3. systemd 활성화 확인 --------------------------------------------------
log "[3/6] systemd 설정을 확인합니다."
if [ ! -d /run/systemd/system ]; then
  if ! sudo grep -qs '^\s*systemd\s*=\s*true' /etc/wsl.conf; then
    log "/etc/wsl.conf 에 systemd 활성화 설정을 추가합니다."
    if sudo grep -qs '^\[boot\]' /etc/wsl.conf; then
      sudo sed -i '/^\[boot\]/a systemd=true' /etc/wsl.conf
    else
      printf '\n[boot]\nsystemd=true\n' | sudo tee -a /etc/wsl.conf >/dev/null
    fi
  fi
  warn "systemd 가 아직 비활성 상태입니다."
  warn "Windows PowerShell 에서 'wsl --shutdown' 실행 후 WSL 을 다시 열고 이 스크립트를 재실행하세요."
  NEEDS_RESTART=1
else
  log "systemd 실행 중 ✔"
  NEEDS_RESTART=0
fi

# --- 4. Node.js 22 LTS -------------------------------------------------------
log "[4/6] Node.js 를 확인합니다."
NODE_OK=0
if command -v node >/dev/null 2>&1; then
  NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"
  if [ "$NODE_MAJOR" -ge 20 ]; then
    log "Node.js $(node -v) 확인 ✔"
    NODE_OK=1
  else
    warn "Node.js $(node -v) 는 너무 낮습니다. 22 LTS 로 교체합니다."
  fi
fi
if [ "$NODE_OK" -eq 0 ]; then
  log "NodeSource 저장소에서 Node.js 22 를 설치합니다."
  curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq nodejs
  log "Node.js $(node -v) 설치 완료 ✔"
fi

# --- 5. Python 가상환경 + 백엔드 의존성 --------------------------------------
log "[5/6] Python 가상환경을 준비합니다."
if [ -d backend/venv ] && [ ! -x backend/venv/bin/python ]; then
  warn "backend/venv 가 Windows 용으로 만들어져 있습니다. 삭제 후 재생성합니다."
  rm -rf backend/venv
fi
if [ ! -x backend/venv/bin/python ]; then
  python3 -m venv backend/venv
fi
backend/venv/bin/python -m pip install --upgrade pip -q
backend/venv/bin/python -m pip install -q -r backend/requirements.txt
log "백엔드 의존성 설치 완료 ✔ ($(backend/venv/bin/python -V))"

# --- 6. 프론트엔드 빌드 ------------------------------------------------------
log "[6/6] 프론트엔드를 빌드합니다."
cd frontend
if [ -f package-lock.json ]; then
  npm ci --no-audit --no-fund
else
  npm install --no-audit --no-fund
fi
npm run build
cd "$PROJECT_DIR"
log "프론트엔드 빌드 완료 ✔ (frontend/dist)"

# --- 마무리 ------------------------------------------------------------------
if [ ! -f .env ]; then
  cp .env.example .env
  warn ".env 가 없어 .env.example 을 복사했습니다. 알림 설정값을 채워 주세요: $PROJECT_DIR/.env"
fi

printf '\n\033[1;32m=== 셋업 완료 ===\033[0m\n'
if [ "$NEEDS_RESTART" -eq 1 ]; then
  printf "다음: 'wsl --shutdown' 후 재진입 → bash scripts/wsl_service_install.sh\n"
else
  printf "다음: bash scripts/wsl_service_install.sh   (systemd 서비스로 상시 운영)\n"
  printf "      또는 ./run_wsl.sh                      (포그라운드로 바로 실행)\n"
fi
