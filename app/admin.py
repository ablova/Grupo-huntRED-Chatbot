# /home/amigro/app/admin.py

import json
from django.urls import path, reverse
from django.contrib import admin
from django.utils.html import format_html
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import (
    MetaAPI, WhatsAppAPI, TelegramAPI, MessengerAPI, InstagramAPI,
    Person, Pregunta, Worker, Buttons, Etapa, SubPregunta, GptApi,
    SmtpConfig, Chat, FlowModel
)

# Definición personalizada del AdminSite
class CustomAdminSite(admin.AdminSite):
    site_header = "Amigro Admin"
    site_title = "Amigro Admin Portal"
    index_title = "Bienvenido a Amigro.org parte de Grupo huntRED®"

    def each_context(self, request):
        context = super().each_context(request)
        context['admin_css'] = 'admin/css/custom_admin.css'  # Estilos personalizados, si tienes alguno.
        return context

admin_site = CustomAdminSite(name='custom_admin')

admin.site.site_header = "Amigro Admin"
admin.site.site_title = "Amigro Admin Portal"
admin.site.index_title = "Bienvenido a Amigro.org parte de Grupo huntRED®"

class SubPreguntaAdmin(admin.ModelAdmin):
    list_display = ('name', 'option', 'decision_si', 'decision_no')

    def decision_si(self, obj):
        return obj.decision.get('yes', 'No definido')

    def decision_no(self, obj):
        return obj.decision.get('no', 'No definido')

    decision_si.short_description = 'Decisión (Sí)'
    decision_no.short_description = 'Decisión (No)'

# Modelo personalizado de FlowModelAdmin con botón para editar el flujo
class FlowModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'edit_flow_button')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:flowmodel_id>/edit-flow/', self.admin_site.admin_view(self.edit_flow), name='edit_flow'),
            path('save_flow/', self.admin_site.admin_view(self.save_flow), name='save_flow'),
            path('load_flow/', self.admin_site.admin_view(self.load_flow), name='load_flow'),
        ]
        return custom_urls + urls

    def edit_flow_button(self, obj):
        return format_html('<a class="button" href="{}">Editar Flujo</a>', reverse('admin:edit_flow', args=[obj.id]))
    
    edit_flow_button.short_description = 'Editar Flujo'
    edit_flow_button.allow_tags = True  # Deprecated en Django >1.9, pero puedes mantenerlo para compatibilidad

    @csrf_exempt
    @require_http_methods(["POST"])
    def save_flow(self, request):
        """
        Guarda el flujo enviado desde el frontend.
        """
        try:
            data = json.loads(request.body)
            flowmodel_id = data.get('flowmodel_id')
            nodes = data.get('nodes', [])
            links = data.get('links', [])
            flow = get_object_or_404(FlowModel, id=flowmodel_id)
            flow.flow_data_json = json.dumps({'nodes': nodes, 'links': links})
            flow.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    @csrf_exempt
    @require_http_methods(["GET"])
    def load_flow(self, request):
        """
        Carga el flujo desde la base de datos.
        """
        try:
            flowmodel_id = request.GET.get('flowmodel_id')
            flow = get_object_or_404(FlowModel, id=flowmodel_id)
            flow_data = json.loads(flow.flow_data_json) if flow.flow_data_json else {}
            return JsonResponse(flow_data)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    def edit_flow(self, request, flowmodel_id):
        """
        Renderiza la plantilla de edición del flujo.
        """
        flow = get_object_or_404(FlowModel, id=flowmodel_id)
        return render(request, 'admin/chatbot_flow.html', {'flow': flow})

admin.site.register(FlowModel, FlowModelAdmin)

# Registro de otros modelos
admin.site.register(WhatsAppAPI)
admin.site.register(TelegramAPI)
admin.site.register(MessengerAPI)
admin.site.register(InstagramAPI)
admin.site.register(MetaAPI)
admin.site.register(Pregunta)
#admin.site.register(ChatState)
admin.site.register(Person)
admin.site.register(Worker)
admin.site.register(Buttons)
admin.site.register(Etapa)
admin.site.register(SubPregunta, SubPreguntaAdmin)
admin.site.register(GptApi)
admin.site.register(SmtpConfig)
admin.site.register(Chat)
