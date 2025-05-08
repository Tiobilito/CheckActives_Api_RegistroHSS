import threading
from config import AUTH_TOKEN_EXPIRATION

# Para tokens de autenticación
active_auth_tokens = {}
auth_token_lock = threading.Lock()

# Diccionario para almacenar los temporizadores activos
active_timers = {}

# Bloqueo para manejar los temporizadores activos
timer_lock = threading.Lock()

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
