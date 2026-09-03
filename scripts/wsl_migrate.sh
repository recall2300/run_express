#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Windows 드라이브(/mnt/c/...)에 있는 프로젝트를 WSL 네이티브 파일시스템으로 이전
#   - .env / config.json / profiles.json 등 git 에 없는 운영 파일도 함께 복사
#   - Windows 전용 산출물(venv, node_modules, dist, __pycache__)은 제외 후 재생성
#   - CRLF 줄바꿈 정리 및 실행 권한 복구
#
# 사용법:
#   bash scripts/wsl_migrate.sh                 # 스크립트가 있는 위치를 원본으로 사용
#   bash scripts/wsl_migrate.sh <원본> [대상]    # 경로 직접 지정
# ---------------------------------------------------------------------------
set -euo pipefail

log()  { printf '\n\033[1;36m[migrate]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*"; }
die()  { printf '\n\033[1;31m[error]\033[0m %s\n' "$*" >&2; exit 1; }

grep -qi microsoft /proc/version 2>/dev/null \
  || die "이 스크립트는 WSL 안에서 실행해야 합니다."

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="${1:-$SELF_DIR}"
DEST="${2:-$HOME/project/run-express}"

SRC="$(cd "$SRC" && pwd)"
[ -f "$SRC/backend/main.py" ] || die "원본 경로가 run-express 프로젝트가 아닙니다: $SRC"

case "$SRC" in
  /mnt/*) : ;;
  *) die "원본($SRC)이 이미 WSL 네이티브 경로입니다. 이전할 필요가 없습니다." ;;
esac
[ "$SRC" != "$DEST" ] || die "원본과 대상이 같습니다."

command -v rsync >/dev/null 2>&1 \
  || die "rsync 가 없습니다. 'sudo apt-get install -y rsync' 후 다시 실행하세요."

log "원본: $SRC"
log "대상: $DEST"

if [ -e "$DEST" ]; then
  warn "대상 경로가 이미 존재합니다. 내용이 덮어쓰기 됩니다."
  read -r -p "계속할까요? [y/N] " ans
  case "$ans" in [yY]*) ;; *) die "취소했습니다." ;; esac
fi

mkdir -p "$DEST"

log "[1/4] 파일을 복사합니다..."
rsync -a --human-readable --info=progress2 \
  --exclude 'backend/venv/' \
  --exclude 'frontend/node_modules/' \
  --exclude 'frontend/dist/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '.pytest_cache/' \
  "$SRC/" "$DEST/"

cd "$DEST"

log "[2/4] 줄바꿈(CRLF -> LF)을 정리합니다."
while IFS= read -r -d '' f; do
  if grep -qU $'\r' "$f" 2>/dev/null; then
    sed -i 's/\r$//' "$f"
    printf '  fixed: %s\n' "${f#./}"
  fi
done < <(find . -path ./.git -prune -o -type f \
           \( -name '*.sh' -o -name '.env' -o -name '.env.example' -o -name '*.service' \) -print0)

log "[3/4] 실행 권한을 복구합니다."
chmod +x ./*.sh scripts/*.sh 2>/dev/null || true

log "[4/4] 운영 파일 존재 여부를 확인합니다."
for f in .env config.json profiles.json; do
  if [ -f "$f" ]; then
    printf '  [OK]   %s\n' "$f"
  else
    printf '  [없음] %s\n' "$f"
  fi
done

printf '\n\033[1;32m=== 이전 완료 ===\033[0m\n'
printf '새 경로: %s\n' "$DEST"
printf 'Windows 탐색기에서는 \\wsl.localhost\<배포판이름>%s 로 접근할 수 있습니다.\n' "$DEST"
printf '\n다음 단계:\n'
printf '  cd %s\n' "$DEST"
printf '  bash scripts/wsl_bootstrap.sh\n'
printf '\n원본(%s)은 그대로 남겨 두었습니다. 새 환경이 정상 동작하는지 확인한 뒤 정리하세요.\n' "$SRC"
