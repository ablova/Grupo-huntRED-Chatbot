from django.contrib import admin
from app.ats.learning.models import Course, LearningPath, Skill, Enrollment

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Administración de Cursos"""
    
    list_display = (
        'name',
        'provider',
        'level',
        'duration',
        'is_active',
        'created_at'
    )
    
    list_filter = (
        'provider',
        'level',
        'is_active',
        'created_at'
    )
    
    search_fields = (
        'name',
        'description',
        'skills__name'
    )
    
    readonly_fields = (
        'created_at',
        'updated_at'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'name',
                'description',
                'provider',
                'url',
                'level'
            )
        }),
        ('Detalles', {
            'fields': (
                'duration',
                'skills',
                'business_unit'
            )
        }),
        ('Precios', {
            'fields': (
                'price',
                'currency'
            )
        }),
        ('Métricas', {
            'fields': (
                'rating',
                'reviews_count'
            )
        }),
        ('Estado', {
            'fields': (
                'is_active',
                'created_at',
                'updated_at'
            )
        })
    )

@admin.register(LearningPath)
class LearningPathAdmin(admin.ModelAdmin):
    """Administración de Rutas de Aprendizaje"""
    
    list_display = (
        'name',
        'user',
        'business_unit',
        'difficulty',
        'status',
        'progress',
        'created_at'
    )
    
    list_filter = (
        'difficulty',
        'status',
        'created_at'
    )
    
    search_fields = (
        'name',
        'description',
        'user__email',
        'target_skills__name'
    )
    
    readonly_fields = (
        'created_at',
        'updated_at',
        'started_at',
        'completed_at'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'name',
                'description',
                'user',
                'business_unit'
            )
        }),
        ('Estructura', {
            'fields': (
                'target_skills',
                'estimated_duration',
                'difficulty'
            )
        }),
        ('Estado', {
            'fields': (
                'status',
                'progress',
                'started_at',
                'completed_at'
            )
        }),
        ('Temporal', {
            'fields': (
                'created_at',
                'updated_at'
            )
        })
    )

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    """Administración de Habilidades"""
    
    list_display = (
        'name',
        'category',
        'level',
        'is_active',
        'created_at'
    )
    
    list_filter = (
        'category',
        'level',
        'is_active',
        'created_at'
    )
    
    search_fields = (
        'name',
        'description',
        'category'
    )
    
    readonly_fields = (
        'created_at',
        'updated_at',
        'last_used'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'name',
                'description',
                'category',
                'level',
                'years_experience'
            )
        }),
        ('Análisis', {
            'fields': (
                'demand_score',
                'growth_potential',
                'related_skills'
            )
        }),
        ('Aprendizaje', {
            'fields': (
                'learning_resources',
                'certification_required',
                'certification_providers'
            )
        }),
        ('Métricas', {
            'fields': (
                'usage_count',
                'last_used'
            )
        }),
        ('Estado', {
            'fields': (
                'is_active',
                'created_at',
                'updated_at'
            )
        })
    )

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    """Administración de Inscripciones"""
    
    list_display = (
        'user',
        'course',
        'status',
        'progress',
        'enrolled_at'
    )
    
    list_filter = (
        'status',
        'enrolled_at',
        'course__provider'
    )
    
    search_fields = (
        'user__email',
        'course__name'
    )
    
    readonly_fields = (
        'enrolled_at',
        'started_at',
        'completed_at',
        'created_at',
        'updated_at'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'user',
                'course',
                'business_unit',
                'status'
            )
        }),
        ('Progreso', {
            'fields': (
                'progress',
                'score'
            )
        }),
        ('Fechas', {
            'fields': (
                'enrolled_at',
                'started_at',
                'completed_at',
                'expires_at'
            )
        }),
        ('Certificación', {
            'fields': (
                'certificate_url',
                'notes'
            )
        }),
        ('Temporal', {
            'fields': (
                'created_at',
                'updated_at'
            )
        })
    ) 