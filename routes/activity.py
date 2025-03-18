import threading
from fastapi import APIRouter
from config import TIMEOUT
from timer_manager import active_timers, timer_lock, timer_callback
from db import update_user_status

router = APIRouter()

@router.get("/")
async def root():
    return {"message": "La API está funcionando"}

@router.post("/activity/{user_id}")
async def report_activity(user_id: str):
    with timer_lock:
        if user_id in active_timers:
            active_timers[user_id].cancel()
            print(f"Timer reiniciado para {user_id}")
        else:
            update_user_status(user_id, True)
        new_timer = threading.Timer(TIMEOUT, timer_callback, args=(user_id,))
        active_timers[user_id] = new_timer
        new_timer.start()
    return {"status": "Activity reported", "user_id": user_id, "timeout": TIMEOUT}

@router.post("/deactivate/{user_id}")
async def immediate_deactivate(user_id: str):
    with timer_lock:
        if user_id in active_timers:
            active_timers[user_id].cancel()
            del active_timers[user_id]
            print(f"Usuario {user_id} desactivado manualmente")
    update_user_status(user_id, False)
    return {"status": "User deactivated", "user_id": user_id}

@router.get("/status")
async def get_status():
    with timer_lock:
        return {
            "active_users": list(active_timers.keys()),
            "total_active": len(active_timers)
        }
