from flask import Blueprint, request, jsonify,current_app
from services.counter_service import countColoniesByQuarters
from flask_jwt_extended import jwt_required
from flask_cors import cross_origin
from middlewares.req_res import get_json, success, bad_request
import uuid
from datetime import datetime
from utils.firebase_config import get_db, get_bucket
from services.counter_service import process_sample_image, get_processed_image_visual

counterBp = Blueprint('samples', __name__, url_prefix="/samples")

def origin():
    # Lee el origen permitido desde la config de la app
    return current_app.config.get("ALLOWED_ORIGIN", "*")

@counterBp.route('/process', methods=['POST'])
@jwt_required()
@cross_origin(supports_credentials=True)
def getColonies():
    try:
        data = get_json()
        file = data.get("file")
        user = data.get("user")
        description = data.get("description")
        sensibility = data.get("sensitivity", type=int, default=50)
        quarters = data.get("quarters",type=int,default=2)
        name = data.get("name",type=str,default= f"sample_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        # extra information
        crop_type = data.get('crop_type', 'default')
        crop_state = data.get('crop_state', 'default')
        notes = data.get('notes', '')
        if not file:
            return bad_request("Archivo no recibido")
        if file:
            # save original image
            bucket = get_bucket()
            blob = bucket.blob(f"samples/{file.filename}")

            contenido = file.read()
            media, img_base64, colonias_totales, colonias_imagenes = result
            return success({
                    'avg': media,
                    'ovi': img_base64,
                    'totals':{
                        'quarters': [f"Cuadrante {i+1}" for i in range(len(colonias_totales))],
                        'values': colonias_totales,
                        'images': colonias_imagenes
                    },
                    'name': name
                }, 200)
    except Exception as e:
        return bad_request(str(e))
    
@counterBp.route('/', methods=['GET'])
def get_samples():
    try:
        db = get_db()
        if not db:
            return jsonify({"error": "Firestore not available"}), 503
            
        samples_ref = db.collection('samples').order_by('created_at', direction='DESCENDING').limit(20)
        docs = samples_ref.stream()
        
        samples_list = [doc.to_dict() for doc in docs]
        return jsonify(samples_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500