from django.contrib import admin
from app.ats.chatbot.models import ChatSession, ChatMessage, ChatTemplate

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    """Administración de Sesiones de Chat"""
    
    list_display = (
        'id',
        'user',
        'status',
        'created_at',
        'last_message_at'
    )
    
    list_filter = (
        'status',
        'created_at',
        'last_message_at'
    )
    
    search_fields = (
        'user__email',
        'context'
    )
    
    readonly_fields = (
        'created_at',
        'last_message_at'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'user',
                'status',
                'context'
            )
        }),
        ('Temporal', {
            'fields': (
                'created_at',
                'last_message_at'
            )
        }),
        ('Métricas', {
            'fields': (
                'message_count',
                'average_response_time'
            )
        })
    )

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    """Administración de Mensajes de Chat"""
    
    list_display = (
        'id',
        'session',
        'sender',
        'type',
        'created_at'
    )
    
    list_filter = (
        'type',
        'created_at'
    )
    
    search_fields = (
        'content',
        'session__user__email'
    )
    
    readonly_fields = (
        'created_at'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'session',
                'sender',
                'type',
                'content'
            )
        }),
        ('Temporal', {
            'fields': (
                'created_at',
            )
        }),
        ('Métricas', {
            'fields': (
                'response_time',
                'processing_time'
            )
        })
    )

@admin.register(ChatTemplate)
class ChatTemplateAdmin(admin.ModelAdmin):
    """Administración de Plantillas de Chat"""
    
    list_display = (
        'name',
        'type',
        'is_active',
        'created_at'
    )
    
    list_filter = (
        'type',
        'is_active'
    )
    
    search_fields = (
        'name',
        'content'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'name',
                'type',
                'is_active'
            )
        }),
        ('Contenido', {
            'fields': (
                'content',
                'variables',
                'conditions'
            )
        })
    ) 