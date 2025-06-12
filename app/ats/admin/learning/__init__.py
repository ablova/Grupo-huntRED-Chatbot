from django.contrib import admin
from app.ats.learning.models import Course, LearningPath, Skill, Enrollment

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Administración de Cursos"""
    
    list_display = (
        'title',
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
        'title',
        'description',
        'skills__name'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'title',
                'description',
                'provider',
                'level'
            )
        }),
        ('Detalles', {
            'fields': (
                'duration',
                'prerequisites',
                'skills',
                'certification'
            )
        }),
        ('Contenido', {
            'fields': (
                'modules',
                'resources',
                'assessments'
            )
        }),
        ('Métricas', {
            'fields': (
                'completion_rate',
                'satisfaction_score',
                'enrollment_count'
            )
        })
    )

@admin.register(LearningPath)
class LearningPathAdmin(admin.ModelAdmin):
    """Administración de Rutas de Aprendizaje"""
    
    list_display = (
        'name',
        'target_role',
        'duration',
        'is_active',
        'created_at'
    )
    
    list_filter = (
        'target_role',
        'is_active',
        'created_at'
    )
    
    search_fields = (
        'name',
        'description',
        'skills__name'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'name',
                'description',
                'target_role',
                'is_active'
            )
        }),
        ('Estructura', {
            'fields': (
                'courses',
                'skills',
                'duration'
            )
        }),
        ('Métricas', {
            'fields': (
                'completion_rate',
                'success_rate',
                'average_time'
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
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'name',
                'description',
                'category',
                'level'
            )
        }),
        ('Relaciones', {
            'fields': (
                'prerequisites',
                'related_skills',
                'courses'
            )
        }),
        ('Métricas', {
            'fields': (
                'demand_score',
                'market_value',
                'learning_difficulty'
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
        'course__title'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'user',
                'course',
                'status'
            )
        }),
        ('Progreso', {
            'fields': (
                'progress',
                'completed_modules',
                'last_activity'
            )
        }),
        ('Evaluación', {
            'fields': (
                'assessments',
                'certificate',
                'feedback'
            )
        })
    ) 