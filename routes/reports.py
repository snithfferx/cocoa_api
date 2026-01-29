import io
from flask import Blueprint, request, send_file, jsonify, g
from utils.firebase_config import get_db
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from datetime import datetime
from middlewares.req_res import get_json, success, bad_request
from middlewares.auth_middleware import firebase_auth_required

reportsBp = Blueprint('reports', __name__)

@reportsBp.route('/monthly', methods=['GET'])
@firebase_auth_required
def generate_monthly_report():
    """
    Genera un reporte de todos los datos de un mes específico.
    Formato: pdf o excel (via query params)
    """
    try:
        month = request.args.get('month') # Formato: YYYY-MM
        fmt = request.args.get('format', 'pdf').lower()
        
        if not month:
            return bad_request("Month parameter is required (YYYY-MM)")

        # 1. Consultar datos de Firestore
        start_date = f"{month}-01"
        end_date = f"{month}-31" 
        
        db = get_db()
        if not db:
            return bad_request("Firestore not available", 503)
            
        samples_ref = db.collection('samples') \
            .where('user_id', '==', g.user_id) \
            .where('date', '>=', start_date) \
            .where('date', '<=', end_date)
        docs = samples_ref.stream()
        data = [doc.to_dict() for doc in docs]
        
        if not data:
            return bad_request("No data found for this month", 404)

        # 2. Generar Reporte
        if fmt == 'excel':
            df = pd.DataFrame(data)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Reporte Mensual')
            output.seek(0)
            return send_file(output, as_attachment=True, download_name=f"reporte_{month}.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            
        elif fmt == 'pdf':
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            p.drawString(100, 750, f"Reporte de Larvas - Mes: {month}")
            p.drawString(100, 730, f"Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            y = 700
            for item in data:
                p.drawString(100, y, f"Fecha: {item.get('date')} - Muestra: {item.get('name')} - Total: {item.get('results', {}).get('total_colonies')}")
                y -= 20
                if y < 50:
                    p.showPage()
                    y = 750
            
            p.save()
            buffer.seek(0)
            return send_file(buffer, as_attachment=True, download_name=f"reporte_{month}.pdf", mimetype='application/pdf')
            
        else:
            return bad_request("Unsupported format. Use 'pdf' or 'excel'.")

    except Exception as e:
        return bad_request(str(e), 500)

@reportsBp.route('/export', methods=['GET'])
@firebase_auth_required
def export_data():
    """
    Exporta datos en formatos Rstudio compatible (JSON/CSV) o TOON.
    """
    fmt = request.args.get('format', 'json').lower()
    try:
        db = get_db()
        if not db:
            return bad_request("Firestore not available", 503)
            
        docs = db.collection('samples') \
            .where('user_id', '==', g.user_id) \
            .limit(500).stream()
        data = [doc.to_dict() for doc in docs]
        
        if fmt == 'json':
            return success(data)
        elif fmt == 'csv':
            df = pd.DataFrame(data)
            output = io.BytesIO()
            df.to_csv(output, index=False)
            output.seek(0)
            return send_file(output, as_attachment=True, download_name="export.csv", mimetype='text/csv')
        else:
            return bad_request("Format not yet implemented", 501)
    except Exception as e:
        return bad_request(str(e), 500)
