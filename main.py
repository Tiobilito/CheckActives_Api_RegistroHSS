from fastapi import FastAPI, HTTPException
from supabase import create_client, Client
import threading
from typing import Dict
import os
from dotenv import load_dotenv
import uvicorn
import smtplib
import ssl
from email.message import EmailMessage
import secrets
from datetime import datetime, timedelta
import pytz  # Asegúrate de importar pytz

# Limpiar las variables de entorno relacionadas
os.environ.pop('EMAIL_PASSWORD', None)

# Cargar variables de entorno
load_dotenv()

# Configuración de Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configuración de la aplicación
TIMEOUT = 60  # En segundos
PORT = 8000
HOST = "0.0.0.0"

# Estructuras para manejar el estado
active_timers: Dict[str, threading.Timer] = {}
timer_lock = threading.Lock()

EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT"))
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM")
print("Correo:", EMAIL_USERNAME)
print("Contraseña:", EMAIL_PASSWORD)  # Solo para pruebas, no dejes esto en producción
print("Desde:", EMAIL_FROM)  # Solo para pruebas, no dejes esto en producción
print(f"EMAIL_PASSWORD: {os.getenv('EMAIL_PASSWORD')}")

# Función para generar un token único
def generate_token():
    return secrets.token_urlsafe(8)

# Función para obtener la hora actual en la zona horaria correcta
def get_local_time():
    # Usar pytz para establecer la zona horaria local
    tz = pytz.timezone("America/Mexico_City")  # Cambia la zona horaria si es necesario
    local_time = datetime.now(tz)  # Obtiene la hora actual en la zona horaria local
    return local_time

# Función para actualizar el token en la base de datos y enviar el correo
async def send_email(to_email: str, subject: str, body: str):
    """Envía un correo electrónico usando smtplib con conexión segura (STARTTLS)."""
    try:
        message = EmailMessage()
        message["From"] = EMAIL_FROM
        message["To"] = to_email
        message["Subject"] = subject
        
        # Formato HTML del correo con la imagen
        html_body = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>Recuperación de Contraseña</title>
          <link rel="icon" href="cid:adaptive-icon.png" type="image/png" />  <!-- Agregar icono -->
        </head>
        <body style="background-color: #eff5f5; margin: 0; padding: 0; font-family: Lucida Grande, Lucida Sans Unicode, Lucida Sans, Helvetica, Arial, sans-serif;">
          <br>
          <div style="padding: 40px; text-align: center;">
            <div style="background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);">
              <div style="line-height: 150%; text-align: center;">
                <img src="cid:adaptive-icon.png" alt="Registro HSS" style="max-width: 100px; height: auto;"/>
              </div>
              <div style="line-height: 150%; text-align: center;">
                <span style="color: #000000; font-size: 30px; font-weight: bold;">Registro HSS</span>
              </div>
              <div style="line-height: 150%; text-align: center;">
                <span style="color: #000000; font-size: 18px;">Recuperación de contraseña</span>
              </div>
              <div style="line-height: 125%; text-align: center; margin-top: 20px;">
                <p style="margin-top: 0px; margin-bottom: 0px; font-weight: bold;">Has solicitado un token para restablecer tu contraseña. Este token expira en 1 hora.</p>
              </div>
              <div style="line-height: 150%; text-align: center; margin-top: 20px;">
                <span style="color: #000000; font-size: 18px; font-weight: bold;">{body}</span>
              </div>
              <div style="line-height: 200%; text-align: center; margin-top: 20px;">
                <span style="font-size: 14px; color: #646464;">Este token es válido solo por 1 hora a partir de este momento. Una vez que uses este token para restablecer tu contraseña, ya no podrás utilizarlo de nuevo.<br>
                Si no realizaste esta solicitud o si tienes alguna duda, por favor contacta con nuestro soporte.<br><br>
                Recuerda que si el token expira, necesitarás generar uno nuevo.<br><br>Saludos</span>
              </div>
              <div style="line-height: 200%; text-align: center; margin-top: 20px;">
                <span style="font-size: 14px; color: #646464;">Registro HSS</span>
              </div>
            </div>
          </div>
        </body>
        </html>
        """
        
        # Establecer contenido como HTML
        message.set_content(f"{body}")  # Texto plano
        message.add_alternative(html_body, subtype='html')  # Agregar alternativa en formato HTML
        
        # Cargar la imagen desde el directorio actual
        image_path = os.path.join(os.getcwd(), 'adaptive-icon.png')  # Ruta a la imagen en el mismo directorio
        
        with open(image_path, 'rb') as f:
            image_data = f.read()
            # Añadir la imagen como un archivo embebido dentro del correo usando el CID
            message.get_payload()[1].add_related(image_data, 'image', 'png', cid='adaptive-icon.png')
        
        # Conectar al servidor SMTP de forma segura usando STARTTLS
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()  # Establece STARTTLS
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            server.send_message(message)

        print(f"Correo enviado a {to_email}")
    except Exception as e:
        print(f"Error enviando correo a {to_email}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al enviar el correo: {str(e)}")

def update_user_status(user_id: str, active: bool):
    """Actualiza el estado del usuario en Supabase a 'Activo' o 'Inactivo'"""
    new_status = "Activo" if active else "Inactivo"
    try:
        # Se actualiza el campo "Status" de la tabla "Usuarios" usando "Codigo" como identificador
        supabase.table("Usuarios").update({"Status": new_status}).eq("Codigo", user_id).execute()
        print(f"Estado actualizado para {user_id}: {new_status}")
    except Exception as e:
        print(f"Error actualizando usuario {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error de base de datos")

def timer_callback(user_id: str):
    """Callback que se ejecuta cuando el timer expira"""
    with timer_lock:
        print(f"Timer expirado para {user_id}")
        if user_id in active_timers:
            del active_timers[user_id]
    try:
        update_user_status(user_id, False)
    except Exception as e:
        print(f"Error en timer_callback para {user_id}: {str(e)}")
        # El error ya se registra en update_user_status

async def lifespan(app: FastAPI):
    # Startup: iniciar timers para usuarios previamente activos
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
    
    yield  # La aplicación permanece en ejecución hasta la señal de apagado
    
    # Shutdown: cancelar todos los timers activos
    print("Apagando aplicación...")
    with timer_lock:
        for user_id, timer in active_timers.items():
            timer.cancel()
            print(f"Timer cancelado para {user_id}")
        active_timers.clear()

# Se crea la aplicación utilizando el manejador de lifespan
app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    """
    Endpoint raíz para indicar que la API está funcionando.
    """
    return {"message": "La API está funcionando"}

@app.post("/activity/{user_id}")
async def report_activity(user_id: str):
    """
    Endpoint para reportar actividad del usuario.
    La primera vez se marca como 'Activo' y se reinicia el timer en cada petición.
    """
    with timer_lock:
        if user_id in active_timers:
            active_timers[user_id].cancel()
            print(f"Timer reiniciado para {user_id}")
        else:
            # Primera vez: actualizar estado a "Activo"
            update_user_status(user_id, True)
        # Crear y arrancar un nuevo timer
        new_timer = threading.Timer(TIMEOUT, timer_callback, args=(user_id,))
        active_timers[user_id] = new_timer
        new_timer.start()
    
    return {"status": "Activity reported", "user_id": user_id, "timeout": TIMEOUT}

@app.post("/deactivate/{user_id}")
async def immediate_deactivate(user_id: str):
    """
    Endpoint para desactivar un usuario inmediatamente actualizando su estado a 'Inactivo'
    """
    with timer_lock:
        if user_id in active_timers:
            active_timers[user_id].cancel()
            del active_timers[user_id]
            print(f"Usuario {user_id} desactivado manualmente")
    
    update_user_status(user_id, False)
    return {"status": "User deactivated", "user_id": user_id}

@app.get("/status")
async def get_status():
    """
    Endpoint para obtener el estado actual de los timers.
    """
    with timer_lock:
        return {
            "active_users": list(active_timers.keys()),
            "total_active": len(active_timers)
        }

if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True, log_level="info")

# Endpoint para enviar el token al correo del usuario
@app.post("/send-reset-token/{user_email}")
async def send_reset_token(user_email: str):
    """
    Endpoint para generar un token de restablecimiento y enviarlo por correo electrónico.
    """
    try:
        # Verificar si el correo electrónico existe en la base de datos
        response = supabase.table("Usuarios").select("Codigo", "Correo").eq("Correo", user_email).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        user_id = response.data[0]["Codigo"]
        
        # Generar un token único y su expiración
        token = generate_token()  # Genera un token único aquí
        expiration_time = get_local_time() + timedelta(hours=1)  # Usar la hora local
        print("Token:", token)

        # Enviar el correo con el token
        subject = "Token de restablecimiento de contraseña"
        body = f"Tu token de restablecimiento es: {token}"
        await send_email(user_email, subject, body)

        return {"status": "Token generado y enviado por correo", "email": user_email}
    
    except Exception as e:
        print(f"Error al generar el token o enviar el correo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al generar el token o enviar el correo: {str(e)}")

@app.get("/verify-token/{user_email}")
async def verify_token(user_email: str):
    """
    Endpoint para verificar si el token de un usuario es válido.
    """
    try:
        token_expiration = get_local_time() + timedelta(hours=1)  # Hora de expiración del token
        current_time = get_local_time()

        # Verificar si el token ha expirado
        if current_time < token_expiration:
            return {"status": "Token válido", "valid": True}
        else:
            return {"status": "Token expirado", "valid": False}
        
    except Exception as e:
        print(f"Error al verificar el token: {str(e)}")
        raise HTTPException(status_code=500, detail="Error en la verificación del token")
