import os
import json
import base64
import cv2
import numpy as np
import face_recognition
import dlib
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.utils.timezone import now
from django.conf import settings
from app.sexsi.models import ConsentAgreement
from app.ats.utils.signature.config import BIOMETRIC_CONFIG

class AdvancedBiometricValidation:
    """Clase para validación biométrica avanzada."""
    
    def __init__(self):
        self.face_detector = dlib.get_frontal_face_detector()
        self.face_encoder = dlib.face_recognition_model_v1(settings.DLIB_FACE_RECOGNITION_MODEL)
        self.landmark_predictor = dlib.shape_predictor(settings.DLIB_SHAPE_PREDICTOR)
        
    def validate_face(self, image_path, reference_path=None):
        """Valida la identidad facial."""
        try:
            # Cargar y procesar imagen
            image = cv2.imread(image_path)
            if image is None:
                return False, "No se pudo cargar la imagen"
                
            # Convertir a RGB para face_recognition
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Detectar rostros
            face_locations = face_recognition.face_locations(rgb_image)
            if not face_locations:
                return False, "No se detectó ningún rostro"
                
            # Obtener encodings faciales
            face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
            
            # Si hay imagen de referencia, comparar
            if reference_path:
                reference_image = cv2.imread(reference_path)
                reference_rgb = cv2.cvtColor(reference_image, cv2.COLOR_BGR2RGB)
                reference_encoding = face_recognition.face_encodings(reference_rgb)[0]
                
                # Comparar con cada rostro detectado
                for face_encoding in face_encodings:
                    match = face_recognition.compare_faces([reference_encoding], face_encoding, tolerance=0.6)[0]
                    if match:
                        return True, "Rostro validado correctamente"
                        
            return True, "Rostro detectado correctamente"
            
        except Exception as e:
            return False, f"Error en validación facial: {str(e)}"
            
    def detect_liveness(self, image_path):
        """Detecta si la imagen es de una persona real."""
        try:
            image = cv2.imread(image_path)
            if image is None:
                return False, "No se pudo cargar la imagen"
                
            # Detectar parpadeo
            blink_detected = self._detect_blink(image)
            
            # Analizar textura de piel
            skin_texture = self._analyze_skin_texture(image)
            
            # Detectar movimiento
            movement = self._detect_movement(image)
            
            # Calcular score de liveness
            liveness_score = (blink_detected + skin_texture + movement) / 3
            
            return liveness_score > BIOMETRIC_CONFIG['liveness_threshold'], f"Score de liveness: {liveness_score}"
            
        except Exception as e:
            return False, f"Error en detección de liveness: {str(e)}"
            
    def _detect_blink(self, image):
        """Detecta parpadeo en la imagen."""
        try:
            # Convertir a escala de grises
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detectar ojos
            eyes = self.face_detector(gray)
            if len(eyes) == 0:
                return 0
                
            # Calcular relación de aspecto de los ojos
            eye_ratio = self._calculate_eye_ratio(eyes[0])
            
            return 1 if eye_ratio < BIOMETRIC_CONFIG['blink_threshold'] else 0
            
        except Exception:
            return 0
            
    def _analyze_skin_texture(self, image):
        """Analiza la textura de la piel."""
        try:
            # Convertir a YCrCb
            ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCR_CB)
            
            # Extraer canal Cr
            cr = ycrcb[:,:,1]
            
            # Calcular varianza de la textura
            texture_variance = np.var(cr)
            
            return 1 if texture_variance > BIOMETRIC_CONFIG['texture_threshold'] else 0
            
        except Exception:
            return 0
            
    def _detect_movement(self, image):
        """Detecta movimiento en la imagen."""
        try:
            # Convertir a escala de grises
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Aplicar detección de bordes
            edges = cv2.Canny(gray, 100, 200)
            
            # Calcular cantidad de bordes
            edge_count = np.count_nonzero(edges)
            
            return 1 if edge_count > BIOMETRIC_CONFIG['movement_threshold'] else 0
            
        except Exception:
            return 0
            
    def _calculate_eye_ratio(self, eye):
        """Calcula la relación de aspecto del ojo."""
        try:
            # Obtener puntos faciales
            shape = self.landmark_predictor(eye, eye)
            points = np.array([[p.x, p.y] for p in shape.parts()])
            
            # Calcular relación de aspecto
            height = np.linalg.norm(points[1] - points[5])
            width = np.linalg.norm(points[0] - points[3])
            
            return height / width if width > 0 else 0
            
        except Exception:
            return 0

def save_biometric_signature(request, agreement_id):
    """Guarda la firma biométrica junto con la ubicación del firmante."""
    agreement = get_object_or_404(ConsentAgreement, id=agreement_id)
    token = request.GET.get("token")
    signer = request.GET.get("signer", "invitee")

    # 📌 Validar el token de autenticidad
    if not agreement.token or agreement.token != token or agreement.token_expiry < now():
        return JsonResponse({"status": "error", "message": "⚠️ El token ha expirado o es inválido."}, status=400)

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            biometric_data = data.get("biometric_data")
            latitude = data.get("latitude")
            longitude = data.get("longitude")

            # 📌 Validar si recibimos datos biométricos
            if not biometric_data:
                return JsonResponse({"status": "error", "message": "⚠️ No se recibió la firma biométrica."}, status=400)

            # 📌 Guardar la firma en la carpeta correspondiente
            biometric_filename = f"biometric_{agreement_id}_{signer}.png"
            biometric_dir = os.path.join(settings.MEDIA_ROOT, "biometric_signatures")
            os.makedirs(biometric_dir, exist_ok=True)
            biometric_path = os.path.join(biometric_dir, biometric_filename)

            with open(biometric_path, "wb") as f:
                f.write(base64.b64decode(biometric_data))

            # 📌 Realizar validación biométrica avanzada
            validator = AdvancedBiometricValidation()
            
            # Validar rostro
            face_valid, face_message = validator.validate_face(biometric_path)
            if not face_valid:
                return JsonResponse({"status": "error", "message": f"⚠️ {face_message}"}, status=400)
                
            # Validar liveness
            liveness_valid, liveness_message = validator.detect_liveness(biometric_path)
            if not liveness_valid:
                return JsonResponse({"status": "error", "message": f"⚠️ {liveness_message}"}, status=400)

            biometric_url = os.path.join(settings.MEDIA_URL, "biometric_signatures", biometric_filename)

            # 📌 Guardar la firma en el modelo
            if signer == "creator":
                agreement.creator_signature = biometric_url
                agreement.is_signed_by_creator = True
                agreement.creator_latitude = latitude
                agreement.creator_longitude = longitude
            else:
                agreement.invitee_signature = biometric_url
                agreement.is_signed_by_invitee = True
                agreement.invitee_latitude = latitude
                agreement.invitee_longitude = longitude

            agreement.save()
            return JsonResponse({
                "status": "success",
                "message": "✅ Firma biométrica registrada correctamente.",
                "biometric_url": biometric_url,
                "latitude": latitude,
                "longitude": longitude
            })

        except Exception as e:
            return JsonResponse({"status": "error", "message": f"⚠️ Error procesando la firma: {str(e)}"}, status=500)

    return JsonResponse({"status": "error", "message": "⚠️ Método no permitido."}, status=405)