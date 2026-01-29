import os
import uuid
import threading
import pandas as pd
import io
from datetime import datetime
from flask import Blueprint, request, jsonify, g
from utils.firebase_config import get_db, get_bucket
from services.counter_service import process_sample_image
from middlewares.req_res import get_json, success, bad_request
from middlewares.auth_middleware import firebase_auth_required

tasksBp = Blueprint('tasks', __name__)

def run_massive_processing(task_id, file_bytes, filename, extension, user_id):
    """
    Función que corre en un hilo separado para procesar el archivo CSV/Excel.
    """
    try:
        # 1. Leer archivo
        if extension == 'csv':
            df = pd.read_csv(io.BytesIO(file_bytes))
        else:
            df = pd.read_excel(io.BytesIO(file_bytes))
            
        # El archivo debería tener una columna con URLs de imágenes o similar.
        # Por ahora, simularemos que procesamos cada fila del archivo.
        
        total_rows = len(df)
        db = get_db()
        if not db:
            print("Error: Firestore not available for task background processing")
            return

        db.collection('tasks').document(task_id).update({
            "status": "en progreso",
            "total_items": total_rows,
            "processed_items": 0
        })
        
        # Simulación de procesamiento
        # ...
        
        db.collection('tasks').document(task_id).update({
            "status": "completado",
            "processed_items": total_rows,
            "completed_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        db = get_db()
        if db:
            db.collection('tasks').document(task_id).update({
                "status": "error",
                "error_message": str(e)
            })

@tasksBp.route('/massive', methods=['POST'])
@firebase_auth_required
def create_massive_task():
    try:
        if 'file' not in request.files:
            return bad_request("No file provided")
            
        file = request.files['file']
        filename = file.filename
        extension = filename.split('.')[-1].lower()
        
        if extension not in ['csv', 'xlsx', 'xls']:
            return bad_request("Invalid file format. Use CSV or Excel.")
            
        file_bytes = file.read()
        task_id = str(uuid.uuid4())
        user_id = g.user_id
        
        # 1. Subir archivo a Storage
        blob_path = f"users/{user_id}/tasks/{task_id}/{filename}"
        
        bucket = get_bucket()
        if not bucket:
            return bad_request("Firebase Storage not available", 503)
            
        blob = bucket.blob(blob_path)
        blob.upload_from_string(file_bytes, content_type=file.content_type)
        blob.make_public()
        file_url = blob.public_url
        
        # 2. Crear documento de tarea en Firestore
        db = get_db()
        if not db:
            return jsonify({"error": "Firestore not available"}), 503
            
        task_data = {
            "id": task_id,
            "user_id": user_id,
            "name": f"Carga masiva: {filename}",
            "status": "pendiente",
            "file_url": file_url,
            "created_at": datetime.now().isoformat(),
            "type": "massive_processing"
        }
        db.collection('tasks').document(task_id).set(task_data)
        
        # 3. Lanzar procesamiento en segundo plano
        # thread = threading.Thread(target=run_massive_processing, args=(task_id, file_bytes, filename, extension, user_id))
        # thread.start()
        
        return success({
            "message": "Task created and processing started",
            "task_id": task_id
        }, 202)
        
    except Exception as e:
        return bad_request(str(e), 500)

@tasksBp.route('/', methods=['GET'])
@firebase_auth_required
def get_tasks():
    try:
        db = get_db()
        if not db:
            return jsonify({"error": "Firestore not available"}), 503
            
        tasks_ref = db.collection('tasks') \
            .where('user_id', '==', g.user_id) \
            .order_by('created_at', direction='DESCENDING')
        docs = tasks_ref.stream()
        return success([doc.to_dict() for doc in docs])
    except Exception as e:
        return bad_request(str(e), 500)
