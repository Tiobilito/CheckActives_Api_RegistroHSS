from fastapi import FastAPI
import threading
from config import PORT, HOST, TIMEOUT, supabase
from timer_manager import active_timers, timer_lock, timer_callback
import uvicorn

# Importar routers de endpoints
from routes.activity import router as activity_router
from routes.auth import router as auth_router

app = FastAPI()

# Evento de startup: inicializa timers para usuarios activos previamente
@app.on_event("startup")
async def startup_event():
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

# Evento de shutdown: cancela todos los timers activos
@app.on_event("shutdown")
async def shutdown_event():
    print("Apagando aplicación...")
    with timer_lock:
        for user_id, timer in active_timers.items():
            timer.cancel()
            print(f"Timer cancelado para {user_id}")
        active_timers.clear()

# Incluir los routers de los endpoints
app.include_router(activity_router)
app.include_router(auth_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True, log_level="info")
