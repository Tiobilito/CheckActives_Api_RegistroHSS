from fastapi import APIRouter, HTTPException
from config import supabase
from utils import generate_token
from timer_manager import add_auth_token, verify_auth_token
from email_service import send_email

router = APIRouter()

@router.post("/send-reset-token/{user_email}")
async def send_reset_token(user_email: str):
    try:
        # Verifica si el correo existe en la base de datos
        response = supabase.table("Usuarios").select("Codigo", "Correo").eq("Correo", user_email).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        user_id = response.data[0]["Codigo"]

        # Generar token y guardarlo en el gestor de tokens (con timer de expiración)
        token = generate_token()
        print("Token generado:", token)
        add_auth_token(user_id, token)
        
        subject = "Token de restablecimiento de contraseña"
        body = f"Tu token de restablecimiento es: {token}"
        await send_email(user_email, subject, body)
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
