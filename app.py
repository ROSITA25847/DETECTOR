from flask import Flask, request, jsonify
import os
import cv2
import numpy as np
from PIL import Image
import io
import base64
from utils.detector import ErrorDetector
from utils.telegram_bot import TelegramBot
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Variables globales
detector = None
telegram_bot = None

def initialize_services():
    global detector, telegram_bot
    try:
        # Inicializar detector
        detector = ErrorDetector('models/impresion.pt')
        logger.info("Detector inicializado correctamente")
        
        # Inicializar bot de Telegram
        telegram_token = os.environ.get('8089007271:AAEUKn7JOx56JjREetduUsq8Qw3PFRewuD8')
        chat_id = os.environ.get('-4893597683')
        
        if telegram_token and chat_id:
            telegram_bot = TelegramBot(telegram_token, chat_id)
            logger.info("Bot de Telegram inicializado correctamente")
        else:
            logger.warning("Token de Telegram o Chat ID no configurados")
            
    except Exception as e:
        logger.error(f"Error inicializando servicios: {e}")

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "Servidor de detección de errores en impresión 3D",
        "version": "1.0"
    })

@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "detector": detector is not None,
        "telegram": telegram_bot is not None
    })

@app.route('/detect', methods=['POST'])
def detect_errors():
    try:
        # Verificar que se envió una imagen
        if 'image' not in request.files:
            return jsonify({"error": "No se encontró imagen"}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "Archivo vacío"}), 400
        
        # Leer imagen
        image_bytes = file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convertir a formato OpenCV
        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Detectar errores
        if detector is None:
            return jsonify({"error": "Detector no inicializado"}), 500
        
        results = detector.detect(opencv_image)
        
        response_data = {
            "timestamp": request.form.get('timestamp', ''),
            "raspberry_id": request.form.get('raspberry_id', 'unknown'),
            "errors_detected": results['errors'],
            "confidence_scores": results['confidences'],
            "total_errors": len(results['errors'])
        }
        
        # Enviar alerta por Telegram si hay errores
        if results['errors'] and telegram_bot:
            error_message = f"🚨 ERRORES DETECTADOS 🚨\n"
            error_message += f"Raspberry ID: {response_data['raspberry_id']}\n"
            error_message += f"Timestamp: {response_data['timestamp']}\n"
            error_message += f"Errores encontrados:\n"
            
            for i, error in enumerate(results['errors']):
                confidence = results['confidences'][i]
                error_message += f"• {error.upper()}: {confidence:.2f}%\n"
            
            telegram_bot.send_alert(error_message)
        
        logger.info(f"Procesamiento completado: {len(results['errors'])} errores detectados")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error procesando imagen: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    initialize_services()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)