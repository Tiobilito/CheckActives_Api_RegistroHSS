import asyncio
from fastapi import APIRouter, HTTPException
from config import supabase
from utils import generate_token
from timer_manager import add_auth_token, verify_auth_token, active_auth_tokens, auth_token_lock
from email_service import send_email

router = APIRouter()

@router.post("/send-reset-token/{user_email}")
async def send_reset_token(user_email: str):
    try:
        # Verificar si el correo existe en la base de datos
        response = supabase.table("Usuarios").select("Codigo", "Correo").eq("Correo", user_email).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        user_id = response.data[0]["Codigo"]

        # Verificar si ya existe una solicitud activa para este usuario
        with auth_token_lock:
            for t, info in active_auth_tokens.items():
                if info["user_id"] == user_id:
                    # Si ya hay una solicitud activa, no se vuelve a enviar el email
                    raise HTTPException(
                        status_code=400,
                        detail="Ya tienes una solicitud activa. Revisa tu correo."
                    )

        # Generar token y agregarlo al gestor de tokens con timer de expiración
        token = generate_token()
        print("Token generado:", token)
        add_auth_token(user_id, token)

        subject = "Token de restablecimiento de contraseña"
        body = f"Tu token de restablecimiento es: {token}"
        # Ejecuta la función de envío de correo en un hilo separado para que sea awaitable
        await asyncio.to_thread(send_email, user_email, subject, body)

        return {"status": "Token generado y enviado por correo", "email": user_email}
    except Exception as e:
        print(f"Error al generar el token o enviar el correo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al generar el token o enviar el correo: {str(e)}")

@router.get("/verify-token/{token}")
async def verify_token(token: str):
    try:
        user_id = verify_auth_token(token)
        if user_id:
            return {"status": "Token válido", "user_id": user_id}
        else:
            return {"status": "Token expirado o inválido", "user_id": None}
    except Exception as e:
        print(f"Error al verificar el token: {str(e)}")
        raise HTTPException(status_code=500, detail="Error en la verificación del token")

@router.post("/remove-token/{token}")
async def remove_token(token: str):
    """
    Endpoint para eliminar el token activo asociado al cambio de contraseña.
    Se espera que la app lo invoque una vez que el cambio de contraseña se haya realizado.
    """
    try:
        with auth_token_lock:
            if token in active_auth_tokens:
                del active_auth_tokens[token]
                print(f"Token {token} eliminado tras el cambio de contraseña.")
                return {"status": "Token eliminado"}
            else:
                raise HTTPException(status_code=404, detail="Token no encontrado")
    except Exception as e:
        print(f"Error eliminando el token: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error eliminando el token: {str(e)}")
