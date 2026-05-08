import asyncio
import json
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from .korail_manager import KorailManager
from .srt_manager import SrtManager

app = FastAPI(title="runKTX API", description="Korail/SRT Reservation Macro API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CONFIG_FILE = "config.json"
PROFILES_FILE = "profiles.json"

managers = {
    "KTX": KorailManager(),
    "SRT": SrtManager()
}

class MacroConfig(BaseModel):
    korail_id: str = ""
    korail_pw: str = ""
    srt_id: str = ""
    srt_pw: str = ""
    dep: str
    arr: str
    date: str
    time: str = ""
    train_no: str = ""
    train_name: str = ""
    phone_number: str = ""
    profile_name: str = ""
    train_type: str = ""
    duration: str = ""
    seat_type: str = "general"
    price: str = ""

@app.post("/api/search/{train_type}")
async def search_trains(train_type: str, config: MacroConfig):
    if train_type not in managers:
        raise HTTPException(status_code=400, detail="Invalid train_type")
    
    # Use asyncio.to_thread to avoid blocking the event loop
    trains = await asyncio.to_thread(managers[train_type].get_train_list, config)
    return {"status": "success", "trains": trains}

@app.get("/api/status")
async def get_status():
    return {
        "KTX": {
            "is_running": managers["KTX"].is_running,
            "logs": managers["KTX"].logs,
            "target_train_no": managers["KTX"].target_train_no,
            "target_train_name": managers["KTX"].target_train_name
        },
        "SRT": {
            "is_running": managers["SRT"].is_running,
            "logs": managers["SRT"].logs,
            "target_train_no": managers["SRT"].target_train_no,
            "target_train_name": managers["SRT"].target_train_name
        }
    }

@app.post("/api/start/{train_type}")
async def start_macro(train_type: str, config: MacroConfig):
    if train_type not in managers:
        raise HTTPException(status_code=400, detail="Invalid train_type")
    
    manager = managers[train_type]
    if manager.is_running:
        return {"status": "error", "message": "Macro is already running"}
    
    # Save last used config
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config.model_dump(), f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Failed to save config: {e}")
    
    # Start background task
    asyncio.create_task(manager.run_macro(config))
    return {"status": "success", "message": f"{train_type} Macro started"}

@app.post("/api/stop/{train_type}")
async def stop_macro(train_type: str):
    if train_type not in managers:
        raise HTTPException(status_code=400, detail="Invalid train_type")
    
    manager = managers[train_type]
    if manager.is_running:
        manager.stop_macro()
        return {"status": "success", "message": "Macro stopping"}
    return {"status": "error", "message": "Macro is not running"}

@app.get("/api/config")
def get_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except (json.JSONDecodeError, ValueError):
                return {}
    return {}

def get_all_profiles():
    if os.path.exists(PROFILES_FILE):
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except (json.JSONDecodeError, ValueError):
                return {}
    return {}

def save_profiles(profiles_data):
    try:
        with open(PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(profiles_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Failed to save profiles: {e}")

@app.get("/api/profiles/{train_type}")
def api_get_profiles(train_type: str):
    profiles = get_all_profiles()
    type_profiles = profiles.get(train_type, {})
    return {"status": "success", "profiles": type_profiles}

@app.post("/api/profiles/{train_type}/{profile_name}")
def api_save_profile(train_type: str, profile_name: str, config: dict):
    profiles = get_all_profiles()
    if train_type not in profiles:
        profiles[train_type] = {}
    profiles[train_type][profile_name] = config
    save_profiles(profiles)
    return {"status": "success", "message": f"[{train_type}] Profile {profile_name} saved"}

@app.delete("/api/profiles/{train_type}/{profile_name}")
def api_delete_profile(train_type: str, profile_name: str):
    profiles = get_all_profiles()
    if train_type in profiles and profile_name in profiles[train_type]:
        del profiles[train_type][profile_name]
        save_profiles(profiles)
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Profile not found")

# Mount React Frontend if it exists
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
