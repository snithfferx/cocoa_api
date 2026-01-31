from flask import Blueprint
# from modules.accounts.users.UsersController import read
def read(user_id):
    return {"id": user_id, "username": "dummy_user", "email": "dummy@example.com", "role": "admin"}
from flask_jwt_extended import jwt_required, verify_jwt_in_request, get_jwt
from middlewares.roles import requires_role
from middlewares.req_res import success, bad_request
from flask_cors import cross_origin
from flask import current_app

userBp = Blueprint("userBp", __name__, url_prefix="/user")

@userBp.route("/admin-only", methods=["GET"])
@firebase_auth_required
def only_admins():
    return success({"ok": True, "message": "Acceso autorizado para administradores"})

@userBp.route("/profile", methods=["GET"])
@firebase_auth_required
@cross_origin(supports_credentials=True)
def profile():
    data = get_json()
    id = data.get("id")
    if not id:
        return bad_request("Credenciales inválidas")
    user = read(id)
    if "error" in user:
        return bad_request(user["error"])
    return success(user)

@userBp.route("/me", methods=["GET"])
@firebase_auth_required
@cross_origin(supports_credentials=True)
def me():
    verify_jwt_in_request()
    claims = get_jwt()
    return success({
        "username": claims.get("username"),
        "email": claims.get("email"),
        "role": claims.get("role"),
    })