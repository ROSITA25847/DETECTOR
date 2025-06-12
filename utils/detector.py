import torch
import cv2
import numpy as np
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ErrorDetector:
    def __init__(self, model_path):
        self.model_path = model_path
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.error_classes = {
            0: 'warping',
            1: 'extrusion',
            2: 'desplazamiento',
            3: 'obstruccion',
            4: 'espagueti'
        }
        self.load_model()
    
    def load_model(self):
        try:
            # Cargar modelo YOLOv5
            self.model = torch.hub.load('ultralytics/yolov5', 'custom', 
                                      path=self.model_path, force_reload=True)
            self.model.to(self.device)
            self.model.eval()
            logger.info(f"Modelo cargado desde {self.model_path}")
        except Exception as e:
            logger.error(f"Error cargando modelo: {e}")
            raise
    
    def preprocess_image(self, image):
        """Preprocesar imagen para el modelo"""
        # Redimensionar imagen manteniendo aspecto
        height, width = image.shape[:2]
        max_size = 640
        
        if max(height, width) > max_size:
            if height > width:
                new_height = max_size
                new_width = int(width * (max_size / height))
            else:
                new_width = max_size
                new_height = int(height * (max_size / width))
            
            image = cv2.resize(image, (new_width, new_height))
        
        return image
    
    def detect(self, image, confidence_threshold=0.5):
        """Detectar errores en la imagen"""
        try:
            # Preprocesar imagen
            processed_image = self.preprocess_image(image)
            
            # Realizar inferencia
            results = self.model(processed_image)
            
            # Procesar resultados
            detections = results.pandas().xyxy[0]
            
            errors = []
            confidences = []
            
            for _, detection in detections.iterrows():
                confidence = detection['confidence']
                
                if confidence >= confidence_threshold:
                    class_id = int(detection['class'])
                    error_name = self.error_classes.get(class_id, f'unknown_{class_id}')
                    
                    errors.append(error_name)
                    confidences.append(confidence * 100)
            
            return {
                'errors': errors,
                'confidences': confidences,
                'raw_detections': detections.to_dict('records') if len(detections) > 0 else []
            }
            
        except Exception as e:
            logger.error(f"Error en detección: {e}")
            return {'errors': [], 'confidences': [], 'raw_detections': []}