from modules.accounts.auth.AuthController import (userRegistration, userLogin, userResetPassword, verifyEmail)
from flask import Blueprint, request, jsonify
from utils.firebase_config import get_auth

from flask_cors import cross_origin
from flask import current_app
from middlewares.req_res import get_json, success, bad_request
from modules.accounts.validators.auth import validate_login_payload, validate_reset_payload,validate_reset_form_payload

authBp = Blueprint("authBp", __name__, url_prefix="/auth")

def origin():
    # Lee el origen permitido desde la config de la app
    return current_app.config.get("ALLOWED_ORIGIN", "*")

@authBp.route("/register", methods=["POST"])
@cross_origin(origins=lambda: origin(), supports_credentials=True)
def register():
    data = get_json()

    msg = validate_login_payload(data)
    if not msg[0]:
        return bad_request(msg[1])
    
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")
    response = userRegistration(username, email, password)
    if (response['status'] == 'error'):
        return bad_request(response['message'])
    return success(response['data'], response['code'])

@authBp.route("/login", methods=["POST"])
@cross_origin(origins=lambda: origin(), supports_credentials=True)
def login():
    data = get_json()
    
    msg = validate_login_payload(data)
    if not msg[0]:
        return bad_request(msg[1])

    username = data.get("username")
    password = data.get("password")
    email = data.get("email", None)
    response = userLogin(username, email, password)
    if (response['status'] == 'error'):
        return bad_request(response['message'])
    return success(response['data'], response['code'])

@authBp.route("/reset-password", methods=["POST"])
@cross_origin(origins=lambda: origin(), supports_credentials=True)
def reset_password():
    data = get_json()

    msg = validate_reset_payload(data)
    if not msg[0]:
        return bad_request(msg[1])
    
    email = data.get("email")
    username = data.get("username")
    response = userResetPasswordRequest(email, username)
    if (response['status'] == 'error'):
        return bad_request(response['message'])
    return success(response['data'], response['code'])

@authBp.route("/reset-password-form", methods=["POST"])
@cross_origin(origins=lambda: origin(), supports_credentials=True)
def reset_password_form():
    data = get_json()
    
    msg = validate_reset_form_payload(data)
    if not msg[0]:
        return bad_request(msg[1])

    token = data.get("token")
    password = data.get("password")
    response = userResetPassword(token, password)
    if (response['status'] == 'error'):
        return bad_request(response['message'])
    return success(response['data'], response['code'])

@authBp.route("/verify-email", methods=["POST"])
@cross_origin(origins=lambda: origin(), supports_credentials=True)
def verify_email():
    data = get_json()
    
    if not "token" in data:
        return bad_request("Credenciales inválidas")

    token = data.get("token")
    response = verifyEmail(token)
    if (response['status'] == 'error'):
        return bad_request(response['message'])
    return success(response['data'], response['code'])

@authBp.route("/verify-token", methods=["POST"])
@cross_origin(origins=lambda: origin(), supports_credentials=True)
def verifyToken():
    """
    Verifica un token de ID de Firebase enviado desde el frontend.
    """
    firebase_auth = get_auth()
    if not firebase_auth:
        return jsonify({"error": "Firebase Auth not available. Check server configuration."}), 503

    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "No token provided"}), 401
    
    id_token = auth_header.split('Bearer ')[1]
    
    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        return jsonify({"status": "verified", "uid": uid}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 401
