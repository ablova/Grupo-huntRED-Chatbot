from django.db import models
from django.utils import timezone
from .models import (
    BusinessUnit, Skill, Tier, SkillAnalysis, CandidateSegment, ImpactAnalysis,
    AnalysisReport, Person, Vacante, Application
)
import json
from datetime import timedelta

class MLAnalysis:
    def __init__(self, business_unit):
        self.business_unit = business_unit
        
    def analyze_skill_distribution(self):
        """
        Analiza la distribución de habilidades por tier
        """
        tiers = Tier.objects.filter(
            candidate__business_unit=self.business_unit
        ).select_related('candidate')
        
        distribution = {}
        
        for tier in tiers:
            skills = tier.candidate.skills.all()
            for skill in skills:
                if skill.name not in distribution:
                    distribution[skill.name] = {
                        'frequency': 0,
                        'tiers': {}
                    }
                distribution[skill.name]['frequency'] += 1
                
                if tier.get_tier_display() not in distribution[skill.name]['tiers']:
                    distribution[skill.name]['tiers'][tier.get_tier_display()] = 0
                distribution[skill.name]['tiers'][tier.get_tier_display()] += 1
                
        # Guardar el análisis en SkillAnalysis
        for skill_name, data in distribution.items():
            skill = Skill.objects.get(name=skill_name)
            for tier_name, count in data['tiers'].items():
                tier = Tier.objects.get(candidate__business_unit=self.business_unit, tier=tier_name)
                SkillAnalysis.objects.update_or_create(
                    business_unit=self.business_unit,
                    skill=skill,
                    tier=tier,
                    defaults={
                        'frequency': count,
                        'impact_score': self._calculate_skill_impact(skill, tier)
                    }
                )
                
        return distribution
        
    def _calculate_skill_impact(self, skill, tier):
        """
        Calcula el impacto de una habilidad en un tier específico
        """
        applications = Application.objects.filter(
            user__business_unit=self.business_unit,
            user__skills__name=skill.name,
            user__tier=tier
        )
        
        success_rate = applications.filter(status='hired').count() / applications.count() if applications.count() > 0 else 0
        avg_time = applications.aggregate(Avg('updated_at' - 'applied_at'))['updated_at__avg'] if applications.count() > 0 else timedelta(days=30)
        
        # Normalizar valores
        success_rate_normalized = min(success_rate * 100, 100)
        time_normalized = min((30 - avg_time.days) / 30 * 100, 100)
        
        return (success_rate_normalized * 0.6 + time_normalized * 0.4) / 100
        
    def calculate_candidate_segment(self, candidate):
        """
        Calcula la segmentación del candidato basada en sus habilidades y métricas
        """
        skills = candidate.skills.all()
        skill_count = len(skills)
        
        # Calcular distribución de habilidades
        skills_by_category = {}
        for skill in skills:
            category = skill.category if hasattr(skill, 'category') else 'general'
            skills_by_category[category] = skills_by_category.get(category, 0) + 1
        
        # Calcular métricas de impacto
        applications = Application.objects.filter(user=candidate)
        success_rate = applications.filter(status='hired').count() / applications.count() if applications.count() > 0 else 0
        avg_time = applications.aggregate(Avg('updated_at' - 'applied_at'))['updated_at__avg'] if applications.count() > 0 else timedelta(days=30)
        
        # Determinar segmento
        segment = 'generalist'
        if skill_count > 10 and len(skills_by_category) > 3:
            segment = 'generalist'
        elif skill_count < 5 and len(skills_by_category) == 1:
            segment = 'specialized'
        elif success_rate > 0.7 and avg_time.days < 15:
            segment = 'high_potential'
        elif success_rate > 0.4 and avg_time.days < 30:
            segment = 'mid_potential'
        else:
            segment = 'low_potential'
            
        # Guardar segmentación
        CandidateSegment.objects.update_or_create(
            candidate=candidate,
            defaults={
                'segment': segment,
                'skills_distribution': json.dumps(skills_by_category),
                'impact_metrics': json.dumps({
                    'success_rate': success_rate,
                    'avg_time': avg_time.days
                })
            }
        )
        
        return segment
        
    def generate_impact_analysis(self):
        """
        Genera un análisis de impacto por tier para la unidad de negocio
        """
        tiers = Tier.objects.filter(
            candidate__business_unit=self.business_unit
        ).values('tier').distinct()
        
        for tier_data in tiers:
            tier = tier_data['tier']
            applications = Application.objects.filter(
                user__business_unit=self.business_unit,
                user__tier=tier
            )
            
            # Calcular métricas
            total_applications = applications.count()
            success_rate = applications.filter(status='hired').count() / total_applications if total_applications > 0 else 0
            avg_time = applications.aggregate(Avg('updated_at' - 'applied_at'))['updated_at__avg'] if total_applications > 0 else timedelta(days=30)
            
            # Analizar importancia de habilidades
            skills = Skill.objects.filter(
                candidates__business_unit=self.business_unit,
                candidates__tier=tier
            )
            
            skill_importance = {}
            for skill in skills:
                skill_importance[skill.name] = self._calculate_skill_impact(skill, tier)
            
            # Guardar análisis
            ImpactAnalysis.objects.update_or_create(
                business_unit=self.business_unit,
                tier=tier,
                defaults={
                    'metrics': json.dumps({
                        'success_rate': success_rate,
                        'avg_time': avg_time.days,
                        'total_applications': total_applications
                    }),
                    'skill_importance': json.dumps(skill_importance)
                }
            )
            
        return True
        
    def generate_analysis_report(self, report_type, period_start, period_end):
        """
        Genera un reporte de análisis para un período específico
        """
        if report_type == 'skill_distribution':
            data = self.analyze_skill_distribution()
        elif report_type == 'impact_analysis':
            self.generate_impact_analysis()
            data = ImpactAnalysis.objects.filter(
                business_unit=self.business_unit
            ).values('tier', 'metrics', 'skill_importance')
        elif report_type == 'segmentation':
            candidates = Person.objects.filter(
                business_unit=self.business_unit,
                created_at__range=[period_start, period_end]
            )
            segments = {}
            for candidate in candidates:
                segment = self.calculate_candidate_segment(candidate)
                if segment not in segments:
                    segments[segment] = 0
                segments[segment] += 1
            data = segments
        
        AnalysisReport.objects.create(
            business_unit=self.business_unit,
            report_type=report_type,
            period_start=period_start,
            period_end=period_end,
            data=json.dumps(data)
        )
        
        return True
