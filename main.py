import os
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

# Importar inicialización de Firebase
from utils.firebase_config import initialize_firebase

def create_app():
    load_dotenv()
    
    app = Flask(__name__)
    
    # Configuración de seguridad
    app.config["ALLOWED_ORIGINS"] = os.getenv("ALLOWED_ORIGIN", "*")
    
    # Inicialización de extensiones
    CORS(app, resources={r"/api/*": {"origins": app.config["ALLOWED_ORIGINS"]}}, supports_credentials=True)
    
    # Inicializar Firebase
    initialize_firebase()
    
    # Importar y registrar blueprints
    from routes.samples import samplesBp
    from routes.auth import authBp
    from routes.tasks import tasksBp
    from routes.reports import reportsBp
    from routes.users import usersBp
    
    app.register_blueprint(authBp, url_prefix='/api/auth')
    app.register_blueprint(samplesBp, url_prefix='/api/samples')
    app.register_blueprint(tasksBp, url_prefix='/api/tasks')
    app.register_blueprint(reportsBp, url_prefix='/api/reports')
    app.register_blueprint(usersBp, url_prefix='/api/users')

    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "healthy", "service": "cocoa-api"}), 200

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 6969)))