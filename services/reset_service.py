import os
import secrets
from datetime import datetime, timedelta
from utils.firebase_config import get_db

def get_rotating_reset_token():
    """
    Obtiene o genera un token de reseteo que se actualiza cada 15 días.
    """
    db = get_db()
    if not db:
        return None
        
    config_ref = db.collection('system_config').document('reset_token')
    doc = config_ref.get()
    
    now = datetime.now()
    
    if doc.exists:
        data = doc.to_dict()
        last_update = datetime.fromisoformat(data['last_update'])
        
        # Si han pasado más de 15 días, rotar token
        if now - last_update > timedelta(days=15):
            new_token = secrets.token_urlsafe(32)
            config_ref.update({
                "token": new_token,
                "last_update": now.isoformat()
            })
            return new_token
        else:
            return data['token']
    else:
        # Inicializar token si no existe
        initial_token = secrets.token_urlsafe(32)
        config_ref.set({
            "token": initial_token,
            "last_update": now.isoformat()
        })
        return initial_token

def verify_reset_token(token):
    """
    Verifica si el token proporcionado es el actual.
    """
    current_token = get_rotating_reset_token()
    return current_token == token
