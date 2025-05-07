# main.py
import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import PORT, HOST, supabase
import uvicorn


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

connected_users = {}  # Diccionario temporal para saber qué usuarios están activos

@sio.event
async def connect(sid, environ):
    print(f"🔌 Cliente conectado: {sid}")

@sio.event
async def disconnect(sid):
    print(f" Cliente desconectado: {sid}")
    user_id = None
    for uid, session in connected_users.items():
        if session["sid"] == sid:
            user_id = uid
            break

    if user_id:
        try:
            supabase.table("Usuarios").update({"Status": "Inactivo"}).eq("Codigo", user_id).execute()
            print(f"Usuario {user_id} marcado como Inactivo")
        except Exception as e:
            print(f" Error al actualizar Supabase para {user_id}: {e}")
        del connected_users[user_id]

@sio.event
async def user_status(sid, data):
    user_id = str(data.get("userId"))
    status = data.get("status", "Activo")

    if status.lower() == "activo":
        connected_users[user_id] = {"sid": sid}
        try:
            supabase.table("Usuarios").update({"Status": "Activo"}).eq("Codigo", user_id).execute()
            print(f" Usuario {user_id} marcado como Activo")
        except Exception as e:
            print(f" Error al actualizar Supabase para {user_id}: {e}")

    await sio.emit("server_message", {"msg": f"Estado de {user_id}: {status}"}, to=sid)

# Ejecutar servidor
if __name__ == "__main__":
    uvicorn.run(socket_app, host=HOST, port=PORT, reload=True)
