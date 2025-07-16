from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from app.payroll.models import EmployeeShift, PayrollEmployee
import json

@csrf_exempt
def shift_list(request):
    if request.method == 'GET':
        shifts = list(EmployeeShift.objects.all().values())
        return JsonResponse({'shifts': shifts})
    elif request.method == 'POST':
        data = json.loads(request.body)
        shift = EmployeeShift.objects.create(**data)
        return JsonResponse({'shift': shift.id})

@csrf_exempt
def shift_detail(request, shift_id):
    try:
        shift = EmployeeShift.objects.get(id=shift_id)
    except EmployeeShift.DoesNotExist:
        return JsonResponse({'error': 'Shift not found'}, status=404)
    if request.method == 'GET':
        return JsonResponse({'shift': shift.id})
    elif request.method == 'PUT':
        data = json.loads(request.body)
        for key, value in data.items():
            setattr(shift, key, value)
        shift.save()
        return JsonResponse({'shift': shift.id}) 