# runKTX Technical Documentation

This document provides a technical overview of the **runKTX** project architecture and implementation details for developers.

## 🏗 System Architecture

The project is divided into a FastAPI backend and a React frontend, optimized for deployment in Docker containers (e.g., Synology NAS).

### Backend (Python/FastAPI)
- **`main.py`**: Entry point. Orchestrates manager instances and provides REST APIs.
- **`base_manager.py`**: Contains `BaseTrainManager`, providing shared logic for logging, SMS notifications, and configuration management.
- **`korail_manager.py` / `srt_manager.py`**: Platform-specific implementations using `korail2` and `SRT` libraries.
- **Concurrency**: Synchronous library calls are wrapped in `asyncio.to_thread` to prevent event loop blocking. Macro loops run as background `asyncio` tasks.

### Frontend (React/Vite)
- **`services/api.js`**: Centralized API client using `fetch`.
- **Component Architecture**: Modularized UI components under `src/components/`.
- **Styling**: Vanilla CSS with modern tokens and glassmorphism (defined in `index.css`).

## ⚙️ Configuration & Data

- **`config.json`**: Stores the last used macro configuration.
- **`profiles.json`**: Stores user profiles including platform credentials and phone numbers.
- **`.env`**: Stores sensitive API keys (Solapi).

## 🚀 Key Implementation Details

### Pagination Bypass
The `_fetch_all_trains` method implements a loop to fetch multiple pages of train results by incrementing the search time for each request, ensuring all trains for a day are discovered regardless of platform paging limits.

### SMS Integration
Uses the Solapi SDK for robust notifications. Authentication requires `SOLAPI_API_KEY` and `SOLAPI_API_SECRET` environment variables.

### Session Management
To prevent session leaks in long-running containers, the `requests` session is periodically reset within the manager instances.

## 🛠 Maintenance & Expansion

### Adding a New Platform
1. Inherit from `BaseTrainManager` in `backend/base_manager.py`.
2. Implement `get_train_list` and `run_macro` specific to the new platform.
3. Add the new manager instance to the `managers` dictionary in `main.py`.
4. Add the platform's stations and network constants to the frontend `App.jsx`.

### UI Customization
The design system is managed via CSS variables in `:root` of `src/index.css`.
