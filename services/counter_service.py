import cv2
import numpy as np
import io
import os
import base64
from PIL import Image
from typing import Tuple, List

def process_sample_image(image_bytes, sectors=1, sensitivity=50):
    """
    Procesa una imagen para contar puntos oscuros (larvas/colonias) en cuadrantes.
    """
    # Convertir bytes a imagen OpenCV
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        raise ValueError("No se pudo decodificar la imagen.")

    # Forzado ancho máximo de 800px manteniendo la proporción
    max_width = 800
    if img.shape[1] > max_width:
        ratio = max_width / float(img.shape[1])
        # Redimensionar la imagen a 800x800 píxeles
        dim = (max_width, int(img.shape[0] * ratio))
        img = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)
        #img = cv2.resize(img, (800, 800))

    # Escala de grises y mejora de contraste
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    contrast = improveContrast(gray)
    blurred = cv2.GaussianBlur(contrast, (5, 5), 0)
    
    # 2. Umbralizado
    threshold_value = 255 - int((sensitivity / 100) * 150 + 20) 
    _, thresh = cv2.threshold(blurred, threshold_value, 255, cv2.THRESH_BINARY_INV)
    
    # 3. Morfología
    kernel = np.ones((3, 3), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
    
    # 4. Encontrar contornos
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    points = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if 2 < area < 1000:
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                points.append((cX, cY))
    
    total_count = len(points)
    h, w = gray.shape
    
    # 5. Análisis por sectores (Grilla NxM)
    # Si sectors=4 -> 2x2. Si sectors=1 -> 1x1. Si sectors=9 -> 3x3.
    # Por ahora asumimos raíces cuadradas perfectas o 1.
    cols = int(np.sqrt(sectors))
    if cols * cols < sectors:
        cols += 1
    rows = (sectors + cols - 1) // cols
    
    sector_results = []
    qh, qw = h // rows, w // cols
    
    for r in range(rows):
        for c in range(cols):
            idx = r * cols + c
            if idx >= sectors: break
            
            x_start = c * qw
            y_start = r * qh
            x_end = (c + 1) * qw if c < cols - 1 else w
            y_end = (r + 1) * qh if r < rows - 1 else h
            
            count_in_sector = sum(1 for p in points if x_start <= p[0] < x_end and y_start <= p[1] < y_end)
            
            # Recortar el cuadrante para la vista detallada
            quadrant_img = img[y_start:y_end, x_start:x_end].copy()
            # Opcional: dibujar puntos locales en el recorte
            for p in points:
                if x_start <= p[0] < x_end and y_start <= p[1] < y_end:
                    cv2.circle(quadrant_img, (p[0] - x_start, p[1] - y_start), 5, (0, 0, 255), 2)
            
            sector_results.append({
                "sector": idx + 1,
                "count": count_in_sector,
                "image_b64": imageToBase64(quadrant_img)
            })
            
    counts = [s["count"] for s in sector_results]
    
    # Imagen visual general con grilla y números
    vis_img = visualizeQuarter(img, (rows, cols), counts)
    
    return {
        "total": total_count,
        "points": points,
        "processed_image_b64": imageToBase64(vis_img),
        "sectors_data": sector_results,
        "stats": {
            "mean": float(np.mean(counts)) if counts else 0.0,
            "max": int(np.max(counts)) if counts else 0,
            "min": int(np.min(counts)) if counts else 0
        },
        "grid": {"rows": rows, "cols": cols}
    }

def get_processed_image_visual(image_bytes, points):
    """
    Genera una imagen con los puntos detectados marcados para visualización.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return None

    for (x, y) in points:
        cv2.circle(img, (x, y), 5, (0, 0, 255), 2)
        
    _, buffer = cv2.imencode('.png', img)
    return buffer.tobytes()

def imageToBase64(image: np.ndarray) -> str:
    """Convierte una imagen OpenCV a string Base64."""
    _, buffer = cv2.imencode('.png', image)
    return base64.b64encode(buffer).decode('utf-8')

def improveContrast(image_gray: np.ndarray) -> np.ndarray:
    """Aplica CLAHE para mejorar el contraste local."""
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(image_gray)

def visualizeQuarter(contrast, cuadrantes, totales):
    """Dibuja cuadrantes y sus totales en la imagen."""
    if len(contrast.shape) == 2:
        vis_img = cv2.cvtColor(contrast, cv2.COLOR_GRAY2BGR)
    else:
        vis_img = contrast.copy()
    
    h, w = vis_img.shape[:2]
    qh, qw = h // cuadrantes[0], w // cuadrantes[1]

    idx = 0
    for i in range(cuadrantes[0]):
        for j in range(cuadrantes[1]):
            x, y = j * qw, i * qh
            cv2.rectangle(vis_img, (x, y), (x + qw, y + qh), (0, 255, 0), 1)
            if idx < len(totales):
                texto = str(totales[idx])
                cv2.putText(vis_img, texto, (x + 5, y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            idx += 1
    return vis_img
