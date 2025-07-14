# /home/pablo/app/ats/admin/chatbot/__init__.py
from django.contrib import admin
from app.models import ChatSession, ChatMessage

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    """Administración de Sesiones de Chat"""
    
    list_display = (
        'id',
        'person',
        'status',
        'created_at',
        'updated_at'
    )
    
    list_filter = (
        'status',
        'created_at',
        'updated_at'
    )
    
    search_fields = (
        'person__email',
        'person__nombre'
    )
    
    readonly_fields = (
        'created_at',
        'updated_at'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'person',
                'status'
            )
        }),
        ('Temporal', {
            'fields': (
                'created_at',
                'updated_at'
            )
        })
    )

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    """Administración de Mensajes de Chat"""
    
    list_display = (
        'id',
        'session',
        'is_bot',
        'created_at'
    )
    
    list_filter = (
        'is_bot',
        'created_at'
    )
    
    search_fields = (
        'content',
        'session__person__email'
    )
    
    readonly_fields = (
        'created_at',
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'session',
                'is_bot',
                'content'
            )
        }),
        ('Temporal', {
            'fields': (
                'created_at',
            )
        })
    ) 