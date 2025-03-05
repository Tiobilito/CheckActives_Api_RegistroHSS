from fastapi import FastAPI, HTTPException
from supabase import create_client, Client
import threading
from typing import Dict
import os
from dotenv import load_dotenv
import uvicorn

# Cargar variables de entorno
load_dotenv()

# Configuración de Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configuración de la aplicación
TIMEOUT = 60  # En segundos
PORT = 8000
HOST = "0.0.0.0"

# Estructuras para manejar el estado
active_timers: Dict[str, threading.Timer] = {}
timer_lock = threading.Lock()

def update_user_status(user_id: str, active: bool):
    """Actualiza el estado del usuario en Supabase a 'Activo' o 'Inactivo'"""
    new_status = "Activo" if active else "Inactivo"
    try:
        # Se actualiza el campo "Status" de la tabla "Usuarios" usando "Codigo" como identificador
        supabase.table("Usuarios").update({"Status": new_status}).eq("Codigo", user_id).execute()
        print(f"Estado actualizado para {user_id}: {new_status}")
    except Exception as e:
        print(f"Error actualizando usuario {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error de base de datos")

def timer_callback(user_id: str):
    """Callback que se ejecuta cuando el timer expira"""
    with timer_lock:
        print(f"Timer expirado para {user_id}")
        if user_id in active_timers:
            del active_timers[user_id]
    try:
        update_user_status(user_id, False)
    except Exception as e:
        print(f"Error en timer_callback para {user_id}: {str(e)}")
        # El error ya se registra en update_user_status

async def lifespan(app: FastAPI):
    # Startup: iniciar timers para usuarios previamente activos
    print("Iniciando aplicación...")
    try:
        response = supabase.table("Usuarios").select("Codigo").eq("Status", "Activo").execute()
        for user in response.data:
            user_id = str(user["Codigo"])
            with timer_lock:
                if user_id not in active_timers:
                    timer = threading.Timer(TIMEOUT, timer_callback, args=(user_id,))
                    active_timers[user_id] = timer
                    timer.start()
                    print(f"Timer iniciado para {user_id} al arranque")
    except Exception as e:
        print(f"Error al cargar usuarios activos: {str(e)}")
    
    yield  # La aplicación permanece en ejecución hasta la señal de apagado
    
    # Shutdown: cancelar todos los timers activos
    print("Apagando aplicación...")
    with timer_lock:
        for user_id, timer in active_timers.items():
            timer.cancel()
            print(f"Timer cancelado para {user_id}")
        active_timers.clear()

# Se crea la aplicación utilizando el manejador de lifespan
app = FastAPI(lifespan=lifespan)

@app.post("/activity/{user_id}")
async def report_activity(user_id: str):
    """
    Endpoint para reportar actividad del usuario.
    La primera vez se marca como 'Activo' y se reinicia el timer en cada petición.
    """
    with timer_lock:
        if user_id in active_timers:
            active_timers[user_id].cancel()
            print(f"Timer reiniciado para {user_id}")
        else:
            # Primera vez: actualizar estado a "Activo"
            update_user_status(user_id, True)
        # Crear y arrancar un nuevo timer
        new_timer = threading.Timer(TIMEOUT, timer_callback, args=(user_id,))
        active_timers[user_id] = new_timer
        new_timer.start()
    
    return {"status": "Activity reported", "user_id": user_id, "timeout": TIMEOUT}

@app.post("/deactivate/{user_id}")
async def immediate_deactivate(user_id: str):
    """
    Endpoint para desactivar un usuario inmediatamente actualizando su estado a 'Inactivo'
    """
    with timer_lock:
        if user_id in active_timers:
            active_timers[user_id].cancel()
            del active_timers[user_id]
            print(f"Usuario {user_id} desactivado manualmente")
    
    update_user_status(user_id, False)
    return {"status": "User deactivated", "user_id": user_id}

@app.get("/status")
async def get_status():
    """
    Endpoint para obtener el estado actual de los timers.
    """
    with timer_lock:
        return {
            "active_users": list(active_timers.keys()),
            "total_active": len(active_timers)
        }

if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True, log_level="info")
