#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# run-express 를 WSL systemd 서비스로 등록/시작한다.
#   사용법: bash scripts/wsl_service_install.sh [포트]   (기본 8888)
# ---------------------------------------------------------------------------
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${1:-8888}"
SERVICE_NAME="run-express"
UNIT_SRC="$PROJECT_DIR/scripts/run-express.service"
UNIT_DST="/etc/systemd/system/${SERVICE_NAME}.service"

log()  { printf '\n\033[1;36m[service]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*"; }
die()  { printf '\n\033[1;31m[error]\033[0m %s\n' "$*" >&2; exit 1; }

grep -qi microsoft /proc/version 2>/dev/null \
  || die "이 스크립트는 WSL 안에서 실행해야 합니다."

if [ ! -d /run/systemd/system ]; then
  die "systemd 가 실행 중이 아닙니다.
  1) /etc/wsl.conf 에 아래 내용을 추가하고
       [boot]
       systemd=true
  2) Windows PowerShell 에서 'wsl --shutdown' 실행 후 WSL 재진입
  (scripts/wsl_bootstrap.sh 가 1)까지는 자동으로 처리합니다)"
fi

[ -x "$PROJECT_DIR/backend/venv/bin/python" ] \
  || die "backend/venv 가 없습니다. 먼저 'bash scripts/wsl_bootstrap.sh' 를 실행하세요."
[ -d "$PROJECT_DIR/frontend/dist" ] \
  || warn "frontend/dist 가 없습니다. 웹 UI 없이 API 만 동작합니다. (npm run build 필요)"
[ -f "$UNIT_SRC" ] || die "유닛 템플릿을 찾을 수 없습니다: $UNIT_SRC"

case "$PROJECT_DIR" in
  /mnt/*) warn "프로젝트가 /mnt(Windows 드라이브)에 있습니다. WSL 재시작 시 마운트 시점 문제로 서비스가 실패할 수 있습니다." ;;
esac

log "서비스 사용자 : $USER"
log "작업 디렉터리 : $PROJECT_DIR"
log "포트          : $PORT"

TMP_UNIT="$(mktemp)"
trap 'rm -f "$TMP_UNIT"' EXIT
sed -e "s|__USER__|$USER|g" \
    -e "s|__PROJECT_DIR__|$PROJECT_DIR|g" \
    -e "s|__PORT__|$PORT|g" \
    "$UNIT_SRC" > "$TMP_UNIT"

log "유닛 파일을 설치합니다: $UNIT_DST"
sudo install -m 0644 "$TMP_UNIT" "$UNIT_DST"
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

sleep 2
if systemctl is-active --quiet "$SERVICE_NAME"; then
  printf '\n\033[1;32m=== 서비스 기동 완료 ===\033[0m\n'
  printf 'WSL 내부   : http://localhost:%s\n' "$PORT"
  printf 'Windows    : http://localhost:%s  (WSL2 localhost 포워딩)\n' "$PORT"
else
  warn "서비스가 기동되지 않았습니다. 로그를 확인하세요."
fi

printf '\n자주 쓰는 명령:\n'
printf '  상태   : systemctl status %s\n'        "$SERVICE_NAME"
printf '  로그   : journalctl -u %s -f\n'        "$SERVICE_NAME"
printf '  재시작 : sudo systemctl restart %s\n'  "$SERVICE_NAME"
printf '  중지   : sudo systemctl stop %s\n'     "$SERVICE_NAME"
printf '  해제   : sudo systemctl disable --now %s\n' "$SERVICE_NAME"
