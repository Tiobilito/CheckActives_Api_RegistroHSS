import os
import smtplib
from email.message import EmailMessage
from fastapi import HTTPException
from config import EMAIL_HOST, EMAIL_PORT, EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_FROM

def send_email(to_email: str, subject: str, body: str):
    try:
        message = EmailMessage()
        message["From"] = EMAIL_FROM
        message["To"] = to_email
        message["Subject"] = subject

        # Contenido HTML del correo
        html_body = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>Recuperación de Contraseña</title>
          <link rel="icon" href="cid:.\assets\adaptive-icon.png.png" type="image/png" />
        </head>
        <body style="background-color: #eff5f5; margin: 0; padding: 0; font-family: sans-serif;">
          <div style="padding: 40px; text-align: center;">
            <div style="background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
              <img src="cid:.\assets\adaptive-icon.png.png" alt="Registro HSS" style="max-width: 100px; height: auto;"/>
              <h1>Registro HSS</h1>
              <h2>Recuperación de contraseña</h2>
              <p>Has solicitado un token para restablecer tu contraseña. Este token expira en 1 hora.</p>
              <h3>{body}</h3>
              <p>Este token es válido solo por 1 hora a partir de este momento. Una vez usado, no será válido.<br>
              Si no realizaste esta solicitud, contacta con nuestro soporte.</p>
              <p>Saludos, Registro HSS</p>
            </div>
          </div>
        </body>
        </html>
        """
        message.set_content(body)  # Texto plano
        message.add_alternative(html_body, subtype='html')

        # Cargar imagen para incluir en el correo
        image_path = os.path.join(os.getcwd(), '.\assets\adaptive-icon.png.png')
        with open(image_path, 'rb') as img:
            image_data = img.read()
            message.get_payload()[1].add_related(image_data, 'image', 'png', cid='.\assets\adaptive-icon.png.png')

        # Conexión segura al servidor SMTP usando STARTTLS
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            server.send_message(message)

        print(f"Correo enviado a {to_email}")
    except Exception as e:
        print(f"Error enviando correo a {to_email}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al enviar el correo: {str(e)}")
