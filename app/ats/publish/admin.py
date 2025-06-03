from django.contrib import admin
from app.models import Channel, ChannelType, ChannelCredential, ChannelAnalytics, ChannelSubscription, Bot, BotCommand, BotResponse, JobChannel

@admin.register(ChannelType)
class ChannelTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'active')
    list_filter = ('active',)
    search_fields = ('name', 'description')

@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'active', 'created_at')
    list_filter = ('type', 'active')
    search_fields = ('name', 'identifier')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ChannelCredential)
class ChannelCredentialAdmin(admin.ModelAdmin):
    list_display = ('channel', 'api_key', 'expires_at')
    list_filter = ('channel__type',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ChannelAnalytics)
class ChannelAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('channel', 'date', 'impressions', 'clicks', 'engagement_rate', 'followers_count')
    list_filter = ('channel__type', 'date')
    readonly_fields = ('created_at',)

@admin.register(ChannelSubscription)
class ChannelSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('channel', 'user', 'subscribed_at', 'active')
    list_filter = ('channel__type', 'active')
    readonly_fields = ('subscribed_at',)

@admin.register(Bot)
class BotAdmin(admin.ModelAdmin):
    list_display = ('name', 'channel', 'active', 'created_at')
    list_filter = ('channel__type', 'active')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(BotCommand)
class BotCommandAdmin(admin.ModelAdmin):
    list_display = ('bot', 'command', 'description', 'active')
    list_filter = ('bot__channel__type', 'active')
    readonly_fields = ('created_at',)

@admin.register(BotResponse)
class BotResponseAdmin(admin.ModelAdmin):
    list_display = ('command', 'response_type', 'created_at')
    list_filter = ('command__bot__channel__type', 'response_type')
    readonly_fields = ('created_at',)

@admin.register(JobChannel)
class JobChannelAdmin(admin.ModelAdmin):
    list_display = ('opportunity', 'channel', 'status', 'scheduled_at', 'published_at')
    list_filter = ('status', 'channel__type')
    readonly_fields = ('created_at',)
    actions = ['publish_selected']

    def publish_selected(self, request, queryset):
        """
        Publica las oportunidades seleccionadas
        """
        from app.ats.publish.tasks import publish_job_opportunity
        
        for job_channel in queryset:
            publish_job_opportunity.delay(job_channel.id)
        
        self.message_user(request, f"Se programaron {queryset.count()} publicaciones")
    
    publish_selected.short_description = "Publicar oportunidades seleccionadas"
