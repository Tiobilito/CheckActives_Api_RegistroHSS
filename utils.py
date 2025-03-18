import secrets
from datetime import datetime, timedelta
import pytz

def generate_token():
    return secrets.token_urlsafe(8)

def get_local_time():
    tz = pytz.timezone("America/Mexico_City")  # Ajusta la zona horaria si es necesario
    local_time = datetime.now(tz)
    return local_time
