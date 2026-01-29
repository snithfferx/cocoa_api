from flask import Blueprint, g
from utils.firebase_config import get_db
from middlewares.auth_middleware import firebase_auth_required
from middlewares.req_res import get_json, success, bad_request

usersBp = Blueprint('users', __name__)

@usersBp.route('/profile', methods=['GET'])
@firebase_auth_required
def get_profile():
    db = get_db()
    if not db:
        return bad_request("Firestore not available", 503)
        
    user_ref = db.collection('users').document(g.user_id)
    doc = user_ref.get()
    
    if not doc.exists:
        # Create default profile if it doesn't exist
        default_profile = {
            "uid": g.user_id,
            "email": g.user_email,
            "settings": {
                "theme": "light",
                "accessibility": {
                    "high_contrast": False,
                    "font_size": "medium"
                }
            }
        }
        user_ref.set(default_profile)
        return success(default_profile)
        
    return success(doc.to_dict())

@usersBp.route('/profile', methods=['PUT'])
@firebase_auth_required
def update_profile():
    data = get_json()
    db = get_db()
    if not db:
        return bad_request("Firestore not available", 503)
        
    user_ref = db.collection('users').document(g.user_id)
    
    # We only allow updating settings
    allowed_updates = {}
    if 'settings' in data:
        allowed_updates['settings'] = data['settings']
    if 'display_name' in data:
        allowed_updates['display_name'] = data['display_name']

    if allowed_updates:
        user_ref.set(allowed_updates, merge=True)
        
    return success({"message": "Profile updated", "data": allowed_updates})
