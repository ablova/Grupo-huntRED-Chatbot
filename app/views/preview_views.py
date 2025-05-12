# /home/pablo/app/views/preview_views.py
#
# Vista para el módulo. Implementa la lógica de presentación y manejo de peticiones HTTP.

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.files.storage import default_storage
from django.conf import settings
import json
import logging

from app.models import CartaOferta, Person, Vacante, BusinessUnit
from app.com.utils.signature.pdf_generator import generate_pdf

logger = logging.getLogger(__name__)

@csrf_exempt
def generar_preview(request):
    """
    Genera una vista previa del PDF de la carta de oferta.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Obtener los datos necesarios
            user_id = data.get('user_id')
            vacancy_id = data.get('vacancy_id')
            salary = data.get('salary')
            benefits = data.get('benefits')
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            
            # Validar datos
            if not all([user_id, vacancy_id, salary, benefits, start_date, end_date]):
                return JsonResponse({'error': 'Faltan datos requeridos'}, status=400)
            
            # Obtener objetos
            user = Person.objects.get(id=user_id)
            vacancy = Vacante.objects.get(id=vacancy_id)
            
            # Generar PDF
            context = {
                'user': user,
                'vacancy': vacancy,
                'salary': salary,
                'benefits': benefits,
                'start_date': start_date,
                'end_date': end_date,
                'fecha_generacion': timezone.now(),
                'business_unit': vacancy.business_unit
            }
            
            # Generar PDF
            pdf_path = generate_pdf('preview_carta_oferta', context)
            
            # Leer el PDF generado
            with open(pdf_path, 'rb') as pdf_file:
                pdf_content = pdf_file.read()
            
            # Limpiar el archivo temporal
            try:
                default_storage.delete(pdf_path)
            except:
                pass
            
            # Devolver el PDF como respuesta
            return JsonResponse({
                'success': True,
                'pdf': pdf_content.hex()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        except Person.DoesNotExist:
            return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
        except Vacante.DoesNotExist:
            return JsonResponse({'error': 'Vacante no encontrada'}, status=404)
        except Exception as e:
            logger.error(f"Error generando vista previa: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)
