from fastapi import FastAPI
import threading
from config import PORT, HOST, TIMEOUT, supabase
from timer_manager import active_timers, timer_lock, timer_callback
import uvicorn
from pyngrok import ngrok
import time
from contextlib import asynccontextmanager

# Importar routers de endpoints
from routes.activity import router as activity_router
from routes.auth import router as auth_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    global api_tunnel, ollama_tunnel
    # Startup: inicializa timers para usuarios activos previamente
    print("Iniciando aplicación...")
    try:
        response = supabase.table("Usuarios").select("Codigo").eq("Status", "Activo").execute()
        if response.data:
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
    
    yield  # La aplicación está en ejecución hasta el shutdown

    # Shutdown: cancelar todos los timers activos y cerrar túneles de ngrok
    print("Apagando aplicación...")
    with timer_lock:
        for user_id, timer in active_timers.items():
            timer.cancel()
            print(f"Timer cancelado para {user_id}")
        active_timers.clear()

    try:
        if 'api_tunnel' in globals():
            ngrok.disconnect(api_tunnel.public_url)
        if 'ollama_tunnel' in globals():
            ngrok.disconnect(ollama_tunnel.public_url)
        ngrok.kill()
        print("Túneles de ngrok cerrados correctamente.")
    except Exception as e:
        print(f"Error cerrando túneles de ngrok: {str(e)}")

app = FastAPI(lifespan=lifespan)

# Incluir los routers de los endpoints
app.include_router(activity_router)
app.include_router(auth_router)

if __name__ == "__main__":
    try:
        global api_tunnel, ollama_tunnel
        # Abre túnel para puerto 8000 (API FastAPI)
        api_tunnel = ngrok.connect(8000, "http")
        print(f"🔗 API disponible en: {api_tunnel.public_url}")

        # Abre túnel para puerto 11434 (Ollama)
        ollama_tunnel = ngrok.connect("localhost:11434", "http", host_header="rewrite")
        print(f"🤖 Ollama disponible en: {ollama_tunnel.public_url}")

        # Esperar unos segundos para asegurar conexión
        time.sleep(1)

        # Actualizar tabla URLs en Supabase
        try:
            supabase.table("URLs").update({"url": api_tunnel.public_url}).eq("id", 1).execute()
            supabase.table("URLs").update({"url": ollama_tunnel.public_url}).eq("id", 2).execute()
            print("✅ URLs actualizadas en Supabase")
        except Exception as e:
            print(f"❌ Error actualizando URLs en Supabase: {e}")

        # Iniciar el servidor
        uvicorn.run("main:app", host=HOST, port=PORT, reload=True, log_level="info")
    except Exception as e:
        print(f"❌ Error al iniciar el servidor: {e}")
