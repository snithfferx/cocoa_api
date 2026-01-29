import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, g
from utils.firebase_config import get_db, get_bucket
from services.counter_service import process_sample_image, get_processed_image_visual
from middlewares.req_res import get_json, success, bad_request
from middlewares.auth_middleware import firebase_auth_required
from flask_cors import cross_origin

samplesBp = Blueprint('samples', __name__)

@samplesBp.route('/process', methods=['POST'])
@firebase_auth_required
@cross_origin(supports_credentials=True)
def process_sample():
    """
    Endpoint para procesar una sola imagen.
    """
    try:
        if 'image' not in request.files:
            return bad_request("No image provided")
        
        image_file = request.files['image']
        filename = image_file.filename
        image_bytes = image_file.read()
        
        # Parámetros opcionales
        sectors = int(request.form.get('sectors', 1))
        sensitivity = int(request.form.get('sensitivity', 50))
        sample_name = request.form.get('name', f"sample_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        crop_type = request.form.get('crop_type', 'default')
        crop_state = request.form.get('crop_state', 'default')
        notes = request.form.get('notes', '')

        # 1. Procesar imagen
        results = process_sample_image(image_bytes, sectors=sectors, sensitivity=sensitivity)
        
        # 3. Guardar en Storage (Imagen Original)
        unique_id = str(uuid.uuid4())
        user_id = g.user_id
        original_blob_path = f"users/{user_id}/samples/{unique_id}/original_{filename}"
        
        bucket = get_bucket()
        if not bucket:
            return bad_request("Firebase Storage not available", 503)

        blob = bucket.blob(original_blob_path)
        blob.upload_from_string(image_bytes, content_type=image_file.content_type)
        blob.make_public()
        original_url = blob.public_url

        # 4. Guardar en Firestore
        db = get_db()
        if not db:
            return bad_request("Firestore not available", 503)
            
        sample_data = {
            "id": unique_id,
            "user_id": user_id,
            "name": sample_name,
            "date": datetime.now().strftime('%Y-%m-%d'),
            "time": datetime.now().strftime('%H:%M:%S'),
            "crop_type": crop_type,
            "crop_state": crop_state,
            "original_image_url": original_url,
            "processed_image_b64": results["processed_image_b64"], # Nueva imagen visualizada
            "results": {
                "total_colonies": results["total"],
                "sectors": results["sectors_data"],
                "stats": results["stats"],
                "grid": results["grid"]
            },
            "notes": notes,
            "status": "completado",
            "created_at": datetime.now().isoformat()
        }
        
        db.collection('samples').document(unique_id).set(sample_data)

        return success(sample_data, 201)

    except Exception as e:
        return bad_request(str(e), 500)

@samplesBp.route('/', methods=['GET'])
@firebase_auth_required
@cross_origin(supports_credentials=True)
def get_samples():
    try:
        db = get_db()
        if not db:
            return bad_request("Firestore not available", 503)
            
        samples_ref = db.collection('samples') \
            .where('user_id', '==', g.user_id) \
            .order_by('created_at', direction='DESCENDING').limit(50)
        docs = samples_ref.stream()
        
        samples_list = [doc.to_dict() for doc in docs]
        return success(samples_list)
    except Exception as e:
        return bad_request(str(e), 500)

@samplesBp.route('/<sample_id>', methods=['GET'])
@firebase_auth_required
@cross_origin(supports_credentials=True)
def get_sample(sample_id):
    try:
        db = get_db()
        if not db:
            return bad_request("Firestore not available", 503)
            
        sample_ref = db.collection('samples').document(sample_id)
        doc = sample_ref.get()
        
        if not doc.exists:
            return bad_request("Sample not found", 404)
        
        data = doc.to_dict()
        if data.get('user_id') != g.user_id:
            return bad_request("Unauthorized access to this sample", 403)
            
        return success(data)
    except Exception as e:
        return bad_request(str(e), 500)

@samplesBp.route('/<sample_id>', methods=['PATCH'])
@firebase_auth_required
@cross_origin(supports_credentials=True)
def update_sample(sample_id):
    """
    Endpoint para actualizar una muestra con ediciones manuales (consecuente con consistencia).
    """
    try:
        data = get_json()
        db = get_db()
        if not db:
            return bad_request("Firestore not available", 503)
            
        sample_ref = db.collection('samples').document(sample_id)
        doc = sample_ref.get()
        
        if not doc.exists:
            return bad_request("Sample not found", 404)
        
        existing_data = doc.to_dict()
        if existing_data.get('user_id') != g.user_id:
            return bad_request("Unauthorized access to this sample", 403)
        
        # Preparar campos a actualizar con prefijo 'edited_' para consistencia
        updates = {}
        if 'total_colonies' in data:
            updates['edited_total_colonies'] = data['total_colonies']
        if 'mean' in data:
            updates['edited_mean'] = data['mean']
        if 'max' in data:
            updates['edited_max'] = data['max']
        if 'notes' in data:
            updates['notes'] = data['notes'] # Las notas sí se pueden sobreescribir según acuerdo
            
        if updates:
            sample_ref.update(updates)
            
        return success({"message": "Sample updated", "updates": updates})
    except Exception as e:
        return bad_request(str(e), 500)
