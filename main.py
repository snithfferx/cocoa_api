import os
from dotenv import load_dotenv
# Flask importados
from flask import Flask, jsonify #, g, request, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
# Importar rutas
from routes.auth import authBp
from routes.user import userBp
from routes.counter import counterBp
# Importar inicialización de Firebase
from utils.firebase_config import initialize_firebase

def create_app():
    load_dotenv()
    # Env variables
    ALLOWED_HOST= os.getenv('ALLOWED_ORIGIN')
    # Configuración de seguridad
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET", "super-secret-key") # Cambiar en .env
    app.config["ALLOWED_ORIGINS"] = os.getenv("ALLOWED_ORIGIN", "*")
    app = Flask(__name__)
    jwt = JWTManager(app)
    CORS(app, resources={r"/api/*": {"origins": [ALLOWED_HOST]}}, supports_credentials=True)
    # Inicializar Firebase
    initialize_firebase()
    # app.register_blueprint(authBp)
    # app.register_blueprint(userBp)
    # app.register_blueprint(counterBp)

    # Importar y registrar blueprints
    from routes.samples import samplesBp
    from routes.auth import authBp
    from routes.tasks import tasksBp
    from routes.reports import reportsBp
    app.register_blueprint(authBp, url_prefix='/api/auth')
    app.register_blueprint(samplesBp, url_prefix='/api/samples')
    app.register_blueprint(tasksBp, url_prefix='/api/tasks')
    app.register_blueprint(reportsBp, url_prefix='/api/reports')

    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "healthy", "service": "cocoa-api"}), 200

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 6969)))