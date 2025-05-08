import threading
from db import update_user_status
from config import TIMEOUT, AUTH_TOKEN_EXPIRATION

# Para actividad de usuarios
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

# Para tokens de autenticación
active_auth_tokens = {}
auth_token_lock = threading.Lock()

def auth_timer_callback(token: str):
    with auth_token_lock:
        print(f"Auth token expirado: {token}")
        if token in active_auth_tokens:
            del active_auth_tokens[token]

def add_auth_token(user_id: str, token: str):
    timer = threading.Timer(AUTH_TOKEN_EXPIRATION, auth_timer_callback, args=(token,))
    with auth_token_lock:
        active_auth_tokens[token] = {"user_id": user_id, "timer": timer}
    timer.start()
    print(f"Auth token agregado para el usuario {user_id} con token {token}")

def verify_auth_token(token: str):
    with auth_token_lock:
        if token in active_auth_tokens:
            return active_auth_tokens[token]["user_id"]
        else:
            return None
