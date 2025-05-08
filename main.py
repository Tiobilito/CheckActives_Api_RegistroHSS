from fastapi import FastAPI
import threading
from config import PORT, HOST, supabase
import uvicorn
from pyngrok import ngrok
import time

# Importar routers de endpoints
from routes.activity import router as activity_router
from routes.auth import router as auth_router

app = FastAPI()

# Incluir los routers de los endpoints
app.include_router(activity_router)
app.include_router(auth_router)

if __name__ == "__main__":
    try:
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
