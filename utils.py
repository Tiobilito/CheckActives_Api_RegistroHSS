import secrets
from datetime import datetime
import pytz

def generate_token():
    return secrets.token_urlsafe(8)

def get_local_time():
    tz = pytz.timezone("America/Mexico_City")
    local_time = datetime.now(tz)
    return local_time
