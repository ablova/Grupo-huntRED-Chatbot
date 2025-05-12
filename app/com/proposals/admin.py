from django.contrib import admin
from app.models import Proposal, Opportunity, Vacancy, Person

class ProposalAdmin(admin.ModelAdmin):
    list_display = ('id', 'company', 'created_at', 'pricing_total', 'status')
    list_filter = ('status', 'created_at')
    search_fields = ('company__name', 'vacancies__title')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        """
        Personaliza la consulta para incluir datos relacionados.
        
        Args:
            request: HttpRequest
            
        Returns:
            QuerySet: Conjunto de propuestas
        """
        return super().get_queryset(request).prefetch_related('vacancies')
    
    def pricing_total(self, obj):
        """
        Muestra el total del pricing.
        
        Args:
            obj: Instancia de Proposal
            
        Returns:
            str: Total formateado
        """
        return f"${obj.pricing_total:.2f}"
    pricing_total.short_description = 'Total'

admin.site.register(Proposal, ProposalAdmin)
