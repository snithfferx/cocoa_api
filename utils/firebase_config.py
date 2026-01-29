import os
import firebase_admin
from firebase_admin import credentials, firestore, storage, auth
from dotenv import load_dotenv

load_dotenv()

def initialize_firebase():
    """
    Inicializa Firebase Admin SDK usando una ruta a las credenciales en .env
    o buscando el archivo por defecto (ADC).
    """
    if not firebase_admin._apps:
        cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
        
        try:
            if cred_path and os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred, {
                    'storageBucket': os.getenv("FIREBASE_STORAGE_BUCKET")
                })
            else:
                # Opción por defecto (intentar inicialización sin credenciales para entornos de Google Cloud / ADC)
                # Si no hay cred_path, intentamos ADC pero atrapamos el error si no existe
                firebase_admin.initialize_app(options={
                    'storageBucket': os.getenv("FIREBASE_STORAGE_BUCKET")
                })
        except Exception as e:
            print(f"\033[91mCRITICAL ERROR: Firebase could not be initialized.\033[0m")
            print(f"Details: {e}")
            print(f"Please check your FIREBASE_SERVICE_ACCOUNT_JSON path in .env")
            return None
                
    try:
        return {
            "db": firestore.client(),
            "bucket": storage.bucket(),
            "auth": auth
        }
    except Exception as e:
        print(f"\033[93mWARNING: Firebase services could not be accessed.\033[0m")
        print(f"Error accessing services: {e}")
        return None

# Helper functions to get clients safely
def get_db():
    resources = initialize_firebase()
    return resources["db"] if resources else None

def get_bucket():
    resources = initialize_firebase()
    return resources["bucket"] if resources else None

def get_auth():
    resources = initialize_firebase()
    return resources["auth"] if resources else None
