import requests
import logging

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"
    
    def send_message(self, message):
        """Enviar mensaje de texto"""
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                logger.info("Mensaje enviado correctamente")
                return True
            else:
                logger.error(f"Error enviando mensaje: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error en send_message: {e}")
            return False
    
    def send_alert(self, message):
        """Enviar alerta de error"""
        alert_message = f"⚠️ <b>ALERTA DE IMPRESIÓN 3D</b> ⚠️\n\n{message}"
        return self.send_message(alert_message)
    
    def send_photo(self, photo_path, caption=""):
        """Enviar imagen con caption"""
        try:
            url = f"{self.base_url}/sendPhoto"
            
            with open(photo_path, 'rb') as photo:
                files = {'photo': photo}
                data = {
                    'chat_id': self.chat_id,
                    'caption': caption
                }
                
                response = requests.post(url, files=files, data=data, timeout=30)
                
                if response.status_code == 200:
                    logger.info("Imagen enviada correctamente")
                    return True
                else:
                    logger.error(f"Error enviando imagen: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error en send_photo: {e}")
            return False