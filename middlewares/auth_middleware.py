from functools import wraps
from flask import request, jsonify, g
from utils.firebase_config import get_auth

def firebase_auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Unauthorized", "message": "No token provided"}), 401
        
        id_token = auth_header.split('Bearer ')[1]
        firebase_auth = get_auth()
        
        if not firebase_auth:
            return jsonify({"error": "Service Unavailable", "message": "Firebase Auth not available"}), 503
        
        try:
            decoded_token = firebase_auth.verify_id_token(id_token)
            g.user = decoded_token['uid']
            g.user_email = decoded_token.get('email')
        except Exception as e:
            return jsonify({"error": "Unauthorized", "message": str(e)}), 401
            
        return f(*args, **kwargs)
    
    return decorated_function
