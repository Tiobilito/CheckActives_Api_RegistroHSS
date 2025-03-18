import threading
from db import update_user_status
from config import TIMEOUT

active_timers = {}
timer_lock = threading.Lock()

def timer_callback(user_id: str):
    with timer_lock:
        print(f"Timer expirado para {user_id}")
        if user_id in active_timers:
            del active_timers[user_id]
    try:
        update_user_status(user_id, False)
    except Exception as e:
        print(f"Error en timer_callback para {user_id}: {str(e)}")
