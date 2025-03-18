from fastapi import APIRouter, HTTPException
from config import supabase
from utils import generate_token, get_local_time
from datetime import timedelta
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
        
        # Genera un token y define su expiración (por ejemplo, 1 hora)
        token = generate_token()
        expiration_time = get_local_time() + timedelta(hours=1)
        print("Token:", token)
        
        subject = "Token de restablecimiento de contraseña"
        body = f"Tu token de restablecimiento es: {token}"
        await send_email(user_email, subject, body)
        return {"status": "Token generado y enviado por correo", "email": user_email}
    except Exception as e:
        print(f"Error al generar el token o enviar el correo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al generar el token o enviar el correo: {str(e)}")

@router.get("/verify-token/{user_email}")
async def verify_token(user_email: str):
    try:
        token_expiration = get_local_time() + timedelta(hours=1)
        current_time = get_local_time()
        if current_time < token_expiration:
            return {"status": "Token válido", "valid": True}
        else:
            return {"status": "Token expirado", "valid": False}
    except Exception as e:
        print(f"Error al verificar el token: {str(e)}")
        raise HTTPException(status_code=500, detail="Error en la verificación del token")
