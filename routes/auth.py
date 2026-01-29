from flask import Blueprint, request, jsonify, current_app, make_response
from utils.firebase_config import get_auth
from middlewares.req_res import get_json, success, bad_request
from datetime import datetime, timedelta
from flask_cors import cross_origin

authBp = Blueprint('auth', __name__)

@authBp.route("/register", methods=["POST"])
@cross_origin(supports_credentials=True)
def register():
    data = get_json()
    email = data.get("email")
    password = data.get("password")
    username = data.get("username")

    if not email or not password:
        return bad_request("Email and password are required")

    firebase_auth = get_auth()
    if not firebase_auth:
        return bad_request("Firebase Auth not available", 503)

    try:
        user = firebase_auth.create_user(
            email=email,
            password=password,
            display_name=username
        )
        return success({"message": "User registered successfully", "uid": user.uid, "email": email}, 201)
    except Exception as e:
        return bad_request(str(e))

@authBp.route("/login", methods=["POST"])
@cross_origin(supports_credentials=True)
def login():
    data = get_json()
    id_token = data.get("idToken")
    remember_me = data.get("rememberMe", False)

    if not id_token:
        return bad_request("ID Token is required")

    firebase_auth = get_auth()
    if not firebase_auth:
        return bad_request("Firebase Auth not available", 503)

    try:
        # Set session expiration: 24h by default, 1 week if 'remember me'
        expires_in = timedelta(days=7) if remember_me else timedelta(days=1)
        
        # Create the session cookie. This will also verify the ID token.
        session_cookie = firebase_auth.create_session_cookie(id_token, expires_in=expires_in)
        
        response = make_response(jsonify({
            "status": "success",
            "message": "Login successful",
            "expires_in": expires_in.total_seconds()
        }))
        
        expires = datetime.now() + expires_in
        response.set_cookie(
            'session', session_cookie, expires=expires, httponly=True, secure=True, samesite='Strict'
        )
        return response
    except Exception as e:
        return bad_request(f"Failed to create session cookie: {str(e)}", 401)

@authBp.route("/logout", methods=["POST"])
@cross_origin(supports_credentials=True)
def logout():
    session_cookie = request.cookies.get('session')
    if not session_cookie:
        return success({"message": "Already logged out"})

    firebase_auth = get_auth()
    try:
        decoded_claims = firebase_auth.verify_session_cookie(session_cookie)
        firebase_auth.revoke_refresh_tokens(decoded_claims['sub'])
        response = make_response(jsonify({"status": "success", "message": "Logged out successfully"}))
        response.set_cookie('session', '', expires=0)
        return response
    except Exception:
        # If cookie is invalid or expired, just clear it
        response = make_response(jsonify({"status": "success", "message": "Logged out successfully"}))
        response.set_cookie('session', '', expires=0)
        return response

@authBp.route("/session-verify", methods=["GET"])
def verify_session():
    session_cookie = request.cookies.get('session')
    if not session_cookie:
        return bad_request("No session active", 401)

    firebase_auth = get_auth()
    try:
        decoded_claims = firebase_auth.verify_session_cookie(session_cookie, check_revoked=True)
        return success({"uid": decoded_claims['uid'], "email": decoded_claims.get('email')})
    except Exception as e:
        return bad_request(str(e), 401)

@authBp.route("/reset-password", methods=["POST"])
@cross_origin(supports_credentials=True)
def reset_password():
    data = get_json()
    email = data.get("email")

    if not email:
        return bad_request("Email is required")

    firebase_auth = get_auth()
    try:
        # Firebase Admin SDK provides generate_password_reset_link but doesn't send the email directly.
        # Usually, this is handled on the client side with firebase.auth().sendPasswordResetEmail(email)
        # But we can generate a link if we want to send it via our own email service.
        link = firebase_auth.generate_password_reset_link(email)
        # TODO: Send email with 'link'
        return success({"message": "Password reset link generated (send via email)", "link": link}, 200)
    except Exception as e:
        return bad_request(str(e))
