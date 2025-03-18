from fastapi import HTTPException
from config import supabase

def update_user_status(user_id: str, active: bool):
    new_status = "Activo" if active else "Inactivo"
    try:
        # Actualiza el campo "Status" en la tabla "Usuarios" usando "Codigo" como identificador
        supabase.table("Usuarios").update({"Status": new_status}).eq("Codigo", user_id).execute()
        print(f"Estado actualizado para {user_id}: {new_status}")
    except Exception as e:
        print(f"Error actualizando usuario {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error de base de datos")
