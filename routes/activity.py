from fastapi import APIRouter, HTTPException
from db import update_user_status

router = APIRouter()

# Diccionario para almacenar usuarios activos con su departamento
connected_users = {}

@router.get("/")
async def root():
    return {"message": "La API está funcionando"}

@router.post("/activity/{user_id}")
async def report_activity(user_id: str):
    """
    Reporta la actividad de un usuario.
    """
    update_user_status(user_id, True)
    print(f"Actividad reportada para el usuario {user_id}")
    return {"status": "Activity reported", "user_id": user_id}

@router.post("/deactivate/{user_id}")
async def immediate_deactivate(user_id: str):
    """
    Desactiva manualmente a un usuario.
    """
    update_user_status(user_id, False)
    print(f"Usuario {user_id} desactivado manualmente")
    return {"status": "User deactivated", "user_id": user_id}

@router.get("/status")
async def get_status():
    """
    Devuelve el estado de los usuarios conectados.
    """
    return {
        "active_users": list(connected_users.keys()),
        "total_active": len(connected_users)
    }

# Lógica de manejo de usuarios activos
def get_active_users_by_department(department_id: str):
    """
    Devuelve los usuarios activos de un departamento específico.
    """
    return [
        {"Codigo": user_id, "idDepartamento": info["department_id"]}
        for user_id, info in connected_users.items()
        if info["department_id"] == department_id
    ]

def add_connected_user(user_id: str, sid: str, department_id: str):
    """
    Agrega un usuario activo al diccionario de usuarios conectados.
    """
    connected_users[user_id] = {"sid": sid, "department_id": department_id}
    print(f"Usuario {user_id} agregado al departamento {department_id}")

def remove_connected_user(sid: str):
    """
    Elimina un usuario activo del diccionario de usuarios conectados.
    """
    user_id = None
    for uid, session in connected_users.items():
        if session["sid"] == sid:
            user_id = uid
            break
    if user_id:
        del connected_users[user_id]
        print(f"Usuario {user_id} eliminado de la lista de activos")
