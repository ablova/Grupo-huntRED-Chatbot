from django.contrib import admin
from app.models import Opportunity, Contract, Vacancy, Person

class OpportunityAdmin(admin.ModelAdmin):
    list_display = ('id', 'company', 'title', 'status', 'created_at')
    list_filter = ('status', 'industry', 'location')
    search_fields = ('title', 'company__name', 'location')
    readonly_fields = ('created_at', 'updated_at')

class ContractAdmin(admin.ModelAdmin):
    list_display = ('id', 'proposal', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('proposal__company__name',)
    readonly_fields = ('created_at', 'updated_at')

class VacancyAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'salary', 'location', 'created_at')
    list_filter = ('location', 'seniority_level')
    search_fields = ('title', 'location')
    readonly_fields = ('created_at', 'updated_at')

class PersonAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'phone', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at')

admin.site.register(Opportunity, OpportunityAdmin)
admin.site.register(Contract, ContractAdmin)
admin.site.register(Vacancy, VacancyAdmin)
admin.site.register(Person, PersonAdmin)
