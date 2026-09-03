# 🏃‍♂️ 런특급 (Run Express)

KTX와 SRT의 빈자리를 자동으로 감지하고 예매해 주는 스마트 기차표 예약 매크로입니다.

![Run Express Logo](https://img.shields.io/badge/Run-Express-4f46e5?style=for-the-badge&logo=train)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react)
![Docker](https://img.shields.io/badge/Docker-Supported-2496ED?style=flat-square&logo=docker)

## 주요 기능
- **통합 검색**: KTX와 SRT 열차 스케줄을 한 화면에서 간편하게 조회합니다.
- **자동 예매 (매크로)**: 매진된 열차의 빈자리가 날 때까지 자동으로 새로고침하며 예매를 시도합니다.
- **실시간 알림**: 예매 성공 시 **텔레그램** 또는 **SMS(Solapi)**를 통해 즉시 알림을 발송합니다.
- **프로필 관리**: 자주 사용하는 출발지, 도착지, 계정 정보를 프로필로 저장하여 빠르게 시작할 수 있습니다.
- **모바일 최적화**: 스마트폰에서도 편리하게 사용할 수 있는 프리미엄 반응형 UI를 제공합니다.

## 설치 및 실행 방법

### 1. WSL 운영 (권장 · 현재 운영환경)
WSL2 + Ubuntu 위에서 systemd 서비스로 상시 운영합니다.

```bash
# WSL(Ubuntu) 안에서
bash scripts/wsl_migrate.sh          # Windows 경로 → ~/project/run-express 이전 (최초 1회)
cd ~/project/run-express
bash scripts/wsl_bootstrap.sh        # 패키지·Node 22·venv·프론트엔드 빌드
bash scripts/wsl_service_install.sh  # systemd 서비스 등록 및 시작
```

```powershell
# Windows PowerShell — 로그온 시 WSL 자동 기동
powershell -ExecutionPolicy Bypass -File scripts\wsl_autostart.ps1
```

접속: `http://localhost:8888`
포그라운드로 바로 실행하려면 `./run_wsl.sh` 를 사용합니다.

> 배포판 설치부터 검증·롤백까지 전체 절차는 **[docs/WSL_MIGRATION.md](docs/WSL_MIGRATION.md)** 를 참고하세요.

### 2. Docker를 이용한 실행
Docker가 설치된 환경 어디서든 명령 한 줄로 시작할 수 있습니다. (Synology NAS 등)

1. `.env.example` 파일을 복사하여 `.env` 파일을 만들고 설정값을 입력합니다.
2. 다음 명령어를 실행합니다.
```bash
./run.sh          # Linux / WSL / macOS
```
```powershell
.\run.bat         # Windows
```
3. 웹 브라우저에서 `http://localhost:8888`에 접속합니다.

### 3. Windows 로컬 실행 (레거시)
WSL 전환 이전 방식으로, 호환을 위해 남겨 두었습니다.

1. `run_local.bat`을 실행합니다. (자동으로 가상환경 구축 및 프론트엔드 빌드를 수행합니다.)
2. 웹 브라우저에서 `http://localhost:8888`에 접속합니다.

## 기술 스택
- **Backend**: FastAPI, korail2, SRT-py
- **Frontend**: React, Vite, Vanilla CSS
- **Deployment**: WSL2 + systemd (운영), Docker & Docker Compose (배포용)

## 라이선스
이 프로젝트는 개인 학습 및 편의를 위해 제작되었습니다. 상업적 이용 및 무단 배포로 발생하는 문제에 대한 책임은 사용자에게 있습니다.

---
Developed by [recall2300](https://github.com/recall2300)
