# WSL 운영환경 전환 가이드

Windows 네이티브(`run.bat` / `run_local.bat`, Docker Desktop) 운영을
**WSL2 + Ubuntu 네이티브 + systemd** 운영으로 전환하는 절차입니다.

전환 후 구성은 다음과 같습니다.

| 항목 | 전환 전 | 전환 후 |
|---|---|---|
| 실행 위치 | Windows / Docker Desktop | WSL2 Ubuntu |
| 프로세스 관리 | 콘솔 창 유지 or Docker | systemd (`run-express.service`) |
| 프로젝트 경로 | `C:\Users\recal\Documents\project\run-express` | `~/project/run-express` (WSL 내부) |
| 자동 시작 | 없음 | systemd enable + Windows 작업 스케줄러 |
| 접속 주소 | `http://localhost:8888` | `http://localhost:8888` (동일) |

> 애플리케이션 코드는 이미 플랫폼 중립적이라 수정이 필요 없습니다.
> 전환 대상은 **실행·배포 도구와 운영 방식**입니다.

---

## 0. 사전 확인

현재 이 PC 상태(2026-09-04 기준):

- WSL **2.6.3.0** 설치됨 ✔
- 설치된 배포판: `docker-desktop` 뿐 — **Docker Desktop 전용 유틸리티 VM 이라 앱 운영에 쓸 수 없습니다.**
  → Ubuntu 배포판 설치가 선행되어야 합니다.

```powershell
wsl --version
wsl --list --verbose
```

---

## 1. Ubuntu 설치 (Windows PowerShell)

```powershell
wsl --install -d Ubuntu
```

- 설치 후 자동으로 Ubuntu 콘솔이 열리며 **리눅스 사용자 이름/비밀번호**를 묻습니다.
  (Windows 계정과 무관한 별도 계정입니다. 이 비밀번호는 `sudo` 에 사용되니 기억해 두세요.)
- 재부팅을 요구하면 재부팅 후 다시 진행합니다.
- 기본 배포판을 Ubuntu 로 바꿔 둡니다(현재 기본값이 `docker-desktop` 입니다):

```powershell
wsl --set-default Ubuntu
wsl --list --verbose      # Ubuntu 가 * 표시 + VERSION 2 인지 확인
```

---

## 2. systemd 활성화

WSL 안에서:

```bash
sudo tee -a /etc/wsl.conf >/dev/null <<'EOF'

[boot]
systemd=true
EOF
```

Windows PowerShell 에서 WSL 을 완전히 종료한 뒤 다시 진입합니다.

```powershell
wsl --shutdown
wsl -d Ubuntu
```

확인:

```bash
systemctl is-system-running     # running (또는 degraded) 이면 정상
```

> `scripts/wsl_bootstrap.sh` 가 이 설정을 자동으로 추가해 주지만,
> **`wsl --shutdown` 후 재진입은 반드시 수동으로 해야 합니다.**

---

## 3. 프로젝트를 WSL 내부로 이전

WSL 안에서 현재 Windows 경로로 이동해 이전 스크립트를 실행합니다.

```bash
sudo apt-get update && sudo apt-get install -y rsync
cd /mnt/c/Users/recal/Documents/project/run-express
bash scripts/wsl_migrate.sh
```

- 기본 대상 경로는 `~/project/run-express` 입니다. (`bash scripts/wsl_migrate.sh <원본> <대상>` 으로 변경 가능)
- `.env`, `config.json`, `profiles.json` 등 **git 에 없는 운영 파일도 함께 복사**됩니다.
- `backend/venv`, `frontend/node_modules`, `frontend/dist` 는 Windows 전용 산출물이라 제외되고 다음 단계에서 재생성됩니다.
- CRLF 줄바꿈 정리와 `chmod +x` 도 함께 처리합니다.
- **원본은 삭제하지 않습니다.** 새 환경 검증 후 직접 정리하세요.

> **왜 옮기나요?** `/mnt/c` 는 9p 파일시스템을 거치기 때문에 `npm ci`, `pip install`
> 같은 대량 파일 I/O 가 수 배~수십 배 느리고, 실행 권한·심볼릭 링크 처리에 제약이 있습니다.
> Windows 탐색기에서는 `\wsl.localhost\Ubuntu\home\<사용자>\project\run-express` 로 접근할 수 있습니다.

---

## 4. 의존성 설치 및 빌드

```bash
cd ~/project/run-express
bash scripts/wsl_bootstrap.sh
```

수행 내용:

1. APT 패키지 (`python3-venv`, `git`, `curl`, `build-essential`, `rsync` 등)
2. 타임존 `Asia/Seoul` — 예매 시각 계산에 필수
3. `/etc/wsl.conf` systemd 설정 확인
4. **Node.js 22 LTS** (프로젝트가 Vite 8 을 쓰므로 Node 20.19+ 또는 22.12+ 필요)
5. `backend/venv` 생성 + `requirements.txt` 설치
6. `frontend` 빌드 → `frontend/dist`

`.env` 가 없으면 `.env.example` 을 복사하므로, 알림 설정값을 채워 주세요.

```bash
nano ~/project/run-express/.env
```

동작만 빠르게 확인하려면:

```bash
./run_wsl.sh          # 포그라운드 실행, Ctrl+C 로 종료
```

---

## 5. systemd 서비스 등록 (상시 운영)

```bash
cd ~/project/run-express
bash scripts/wsl_service_install.sh          # 기본 포트 8888
# bash scripts/wsl_service_install.sh 9000   # 포트 변경
```

`scripts/run-express.service` 템플릿의 `__USER__` / `__PROJECT_DIR__` / `__PORT__` 가
실제 값으로 치환되어 `/etc/systemd/system/run-express.service` 로 설치되고,
`enable` + `restart` 까지 수행합니다.

운영 명령:

```bash
systemctl status run-express          # 상태
journalctl -u run-express -f          # 실시간 로그
journalctl -u run-express -n 200      # 최근 200줄
sudo systemctl restart run-express    # 재시작
sudo systemctl stop run-express       # 중지
sudo systemctl disable --now run-express   # 자동 시작 해제 + 중지
```

`Restart=always` 이므로 매크로 프로세스가 죽어도 5초 뒤 자동 복구됩니다.

---

## 6. Windows 부팅 시 자동 시작

WSL2 배포판은 Windows 부팅만으로는 켜지지 않습니다.
로그온 시 배포판을 한 번 깨워 주면 systemd 가 기동되고 서비스도 함께 올라옵니다.

Windows PowerShell 에서:

```powershell
cd C:\Users\recal\Documents\project\run-express
powershell -ExecutionPolicy Bypass -File scripts\wsl_autostart.ps1
```

- 로그온 30초 후 `wsl.exe -d Ubuntu -e /bin/true` 를 실행하는 작업을 등록합니다.
- 배포판 이름이 다르면 `-Distro Ubuntu-24.04` 처럼 지정합니다.
- 해제: `powershell -File scripts\wsl_autostart.ps1 -Remove`
- 즉시 시험: `Start-ScheduledTask -TaskName 'RunExpress-WSL-Autostart'`

> 프로젝트 파일이 WSL 내부에 있으므로, 스크립트를 Windows 쪽에서 실행하려면
> `\wsl.localhost\Ubuntu\home\<사용자>\project\run-express\scripts\wsl_autostart.ps1`
> 경로를 쓰거나, 이전 전 원본 폴더의 스크립트를 그대로 사용하면 됩니다.

---

## 7. 접속

| 위치 | 주소 |
|---|---|
| WSL 내부 | `http://localhost:8888` |
| Windows 브라우저 | `http://localhost:8888` (WSL2 localhost 포워딩) |
| 같은 공유기의 다른 기기 | 아래 포트 프록시 설정 필요 |

WSL2 는 NAT 뒤에 있어 **외부 기기에서는 바로 접속되지 않습니다.**
휴대폰 등에서 접속하려면 관리자 PowerShell 에서:

```powershell
$wslIp = (wsl -d Ubuntu -e hostname -I).Trim().Split()[0]
netsh interface portproxy add v4tov4 listenport=8888 listenaddress=0.0.0.0 connectport=8888 connectaddress=$wslIp
New-NetFirewallRule -DisplayName "run-express 8888" -Direction Inbound -LocalPort 8888 -Protocol TCP -Action Allow
```

WSL IP 는 재부팅마다 바뀌므로 위 명령을 다시 실행해야 합니다.
자주 쓴다면 `%USERPROFILE%\.wslconfig` 에 미러 네트워킹을 켜는 편이 편합니다.

```ini
[wsl2]
networkingMode=mirrored
```

(적용: `wsl --shutdown` 후 재진입. 이 모드에서는 포트 프록시 없이 Windows IP 로 바로 접속됩니다.)

---

## 8. 검증 체크리스트

```bash
systemctl is-active run-express                  # active
curl -s localhost:8888/api/status | head -c 200  # JSON 응답
curl -s -o /dev/null -w '%{http_code}\n' localhost:8888   # 200 (웹 UI)
date                                             # KST 인지 확인
```

- [ ] Windows 브라우저에서 `http://localhost:8888` 접속 및 UI 렌더링
- [ ] 프로필 목록이 그대로 보이는지 (`profiles.json` 이전 확인)
- [ ] 열차 검색 동작
- [ ] 텔레그램/SMS 알림 발송 (`.env` 이전 확인)
- [ ] `wsl --shutdown` → `wsl -d Ubuntu` 후 서비스 자동 기동
- [ ] Windows 재로그온 후 자동 기동

---

## 9. 롤백

WSL 쪽 서비스만 내리면 기존 Windows 실행 방식이 그대로 살아 있습니다.

```bash
sudo systemctl disable --now run-express
```

```powershell
powershell -File scripts\wsl_autostart.ps1 -Remove
# 이후 기존 방식대로 run.bat 또는 run_local.bat 실행
```

원본 Windows 폴더를 지우지 않았다면 데이터 손실은 없습니다.

---

## 10. 알아 둘 점

- **작업 디렉터리 의존성** — `backend/main.py` 는 `config.json` / `profiles.json` 을
  **현재 작업 디렉터리 기준 상대 경로**로 읽고 씁니다. systemd 유닛의
  `WorkingDirectory` 가 프로젝트 루트로 설정되어 있어 정상 동작하지만,
  다른 경로에서 `uvicorn` 을 직접 띄우면 설정 파일을 찾지 못합니다.
- **타임존** — 컨테이너에서 `TZ=Asia/Seoul` 을 주던 것을 WSL 시스템 타임존 +
  유닛의 `Environment=TZ=Asia/Seoul` 로 대체했습니다.
- **Docker 경로 유지** — `Dockerfile` / `docker-compose.yml` 은 그대로 두었습니다.
  Synology NAS 배포 등 기존 용도에 계속 쓸 수 있습니다.
- **민감 파일** — `.env`, `config.json`, `profiles.json` 은 계정 정보를 담고 있고
  `.gitignore` 대상입니다. 이전 후 원본 폴더를 정리할 때 함께 안전하게 삭제하세요.
- **Docker Desktop 과의 공존** — Ubuntu 배포판을 추가해도 `docker-desktop` 배포판은
  그대로 남습니다. Docker Desktop 을 계속 쓰더라도 충돌하지 않습니다.
