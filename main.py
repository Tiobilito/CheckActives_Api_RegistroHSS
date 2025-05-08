from pyngrok import ngrok
import time
import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import PORT, HOST, supabase
import uvicorn
import atexit  # Importar para manejar eventos al cerrar la aplicación


sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir tus routers normales (API REST)
from routes.activity import router as activity_router
from routes.auth import router as auth_router
app.include_router(activity_router)
app.include_router(auth_router)

# Asociar FastAPI con socket.io
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

from routes.activity import add_connected_user, remove_connected_user, get_active_users_by_department

@sio.event
async def connect(sid, environ):
    print(f"🔌 Cliente conectado: {sid}")

@sio.event
async def disconnect(sid):
    print(f" Cliente desconectado: {sid}")
    remove_connected_user(sid)  # Elimina al usuario de la memoria de activos
    await sio.emit("user_disconnected", {"sid": sid})

@sio.event
async def add_active(sid, data):
    """
    Maneja la adición de un usuario activo.
    """
    codigo = str(data.get("Codigo"))
    id_departamento = str(data.get("idDepartamento"))

    add_connected_user(codigo, sid, id_departamento)
    await sio.emit("user_status_updated", {"sid": sid, "Codigo": codigo, "idDepartamento": id_departamento})

@sio.event
async def emit_active_users_by_department(sid, data):
    """
    Envía en tiempo real los usuarios activos de un departamento específico.
    """
    id_departamento = str(data.get("idDepartamento"))
    active_users = get_active_users_by_department(id_departamento)
    await sio.emit("active_users", {"idDepartamento": id_departamento, "active_users": active_users}, to=sid)

# Función para limpiar las URLs en Supabase al cerrar la API
def cleanup_urls():
    try:
        supabase.table("URLs").update({"url": None}).eq("id", 1).execute()
        supabase.table("URLs").update({"url": None}).eq("id", 2).execute()
        print("🧹 URLs limpiadas en Supabase")
    except Exception as e:
        print(f"❌ Error limpiando URLs en Supabase: {e}")

# Registrar la función de limpieza para ejecutarse al cerrar la aplicación
atexit.register(cleanup_urls)

# Validar configuración
if not PORT or not HOST:
    raise ValueError("Las variables de configuración PORT y HOST deben estar definidas en config.py")

# Ejecutar servidor
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
        uvicorn.run("main:socket_app", host=HOST, port=PORT, reload=True)
    except Exception as e:
        print(f"❌ Error al iniciar el servidor: {e}")
