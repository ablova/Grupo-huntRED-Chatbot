from typing import Dict, List, Optional
from django.db.models import Avg, Count
from django.utils import timezone
from datetime import timedelta
from app.models import Proposal, Vacante, Company, BusinessUnit
from app.ats.pricing.models import ServiceCalculation

class RecommendationService:
    def __init__(self):
        self.success_threshold = 80  # Tasa de éxito mínima para recomendaciones
        self.min_positions = 5  # Mínimo de posiciones para considerar métricas

    def get_recommendations(self, company: Company, vacancy: Vacante) -> Dict:
        """
        Genera recomendaciones personalizadas para una vacante.
        
        Args:
            company: Instancia de Company
            vacancy: Instancia de Vacante
            
        Returns:
            Dict: Recomendaciones y métricas
        """
        # Obtener métricas de éxito
        success_metrics = self._get_success_metrics(vacancy)
        
        # Obtener recomendaciones de pricing
        pricing_recommendations = self._get_pricing_recommendations(
            company, vacancy, success_metrics
        )
        
        # Obtener recomendaciones de estructura de pago
        payment_recommendations = self._get_payment_recommendations(
            company, vacancy, success_metrics
        )
        
        # Obtener recomendaciones de addons
        addon_recommendations = self._get_addon_recommendations(
            company, vacancy, success_metrics
        )
        
        return {
            'success_metrics': success_metrics,
            'pricing': pricing_recommendations,
            'payment_structure': payment_recommendations,
            'addons': addon_recommendations
        }

    def _get_success_metrics(self, vacancy: Vacante) -> Dict:
        """
        Obtiene métricas de éxito para puestos similares.
        
        Args:
            vacancy: Instancia de Vacante
            
        Returns:
            Dict: Métricas de éxito
        """
        # Buscar puestos similares en los últimos 6 meses
        similar_positions = Vacante.objects.filter(
            title__icontains=vacancy.title,
            created_at__gte=timezone.now() - timedelta(days=180)
        ).exclude(id=vacancy.id)
        
        if not similar_positions.exists():
            return {
                'success_rate': 0,
                'avg_time_to_fill': 0,
                'total_positions': 0
            }
        
        # Calcular métricas
        total_positions = similar_positions.count()
        filled_positions = similar_positions.filter(status='filled').count()
        avg_time_to_fill = similar_positions.filter(
            status='filled'
        ).aggregate(
            avg_time=Avg('time_to_fill')
        )['avg_time'] or 0
        
        return {
            'success_rate': (filled_positions / total_positions) * 100,
            'avg_time_to_fill': avg_time_to_fill,
            'total_positions': total_positions
        }

    def _get_pricing_recommendations(
        self, company: Company, vacancy: Vacante, metrics: Dict
    ) -> Dict:
        """
        Genera recomendaciones de pricing basadas en métricas.
        
        Args:
            company: Instancia de Company
            vacancy: Instancia de Vacante
            metrics: Métricas de éxito
            
        Returns:
            Dict: Recomendaciones de pricing
        """
        # Obtener historial de pricing de la empresa
        company_history = ServiceCalculation.objects.filter(
            company=company,
            created_at__gte=timezone.now() - timedelta(days=365)
        )
        
        # Calcular promedio de honorarios
        avg_fee = company_history.aggregate(
            avg_fee=Avg('total_fee')
        )['avg_fee'] or 0
        
        # Ajustar según métricas de éxito
        if metrics['success_rate'] > self.success_threshold:
            recommended_fee = avg_fee * 1.1  # Aumentar 10%
        elif metrics['success_rate'] < 50:
            recommended_fee = avg_fee * 0.9  # Reducir 10%
        else:
            recommended_fee = avg_fee
        
        return {
            'recommended_fee': recommended_fee,
            'avg_fee': avg_fee,
            'adjustment_factor': recommended_fee / avg_fee if avg_fee else 1
        }

    def _get_payment_recommendations(
        self, company: Company, vacancy: Vacante, metrics: Dict
    ) -> Dict:
        """
        Genera recomendaciones de estructura de pago.
        
        Args:
            company: Instancia de Company
            vacancy: Instancia de Vacante
            metrics: Métricas de éxito
            
        Returns:
            Dict: Recomendaciones de estructura de pago
        """
        # Obtener historial de estructuras de pago
        payment_history = ServiceCalculation.objects.filter(
            company=company,
            created_at__gte=timezone.now() - timedelta(days=365)
        ).values('payment_structure').annotate(
            count=Count('id')
        ).order_by('-count')
        
        if not payment_history.exists():
            return {
                'recommended_structure': 'standard',
                'confidence': 0
            }
        
        # Obtener estructura más común
        most_common = payment_history.first()
        
        # Calcular confianza basada en métricas
        confidence = min(metrics['success_rate'] / 100, 1)
        
        return {
            'recommended_structure': most_common['payment_structure'],
            'confidence': confidence
        }

    def _get_addon_recommendations(
        self, company: Company, vacancy: Vacante, metrics: Dict
    ) -> List[Dict]:
        """
        Genera recomendaciones de addons.
        
        Args:
            company: Instancia de Company
            vacancy: Instancia de Vacante
            metrics: Métricas de éxito
            
        Returns:
            List[Dict]: Lista de recomendaciones de addons
        """
        # Obtener addons más comunes para puestos similares
        similar_positions = Vacante.objects.filter(
            title__icontains=vacancy.title,
            created_at__gte=timezone.now() - timedelta(days=180)
        )
        
        addon_recommendations = []
        
        # Analizar cada tipo de addon
        for addon_type in ['assessment', 'team_evaluation', 'background_check']:
            # Calcular tasa de uso
            usage_rate = similar_positions.filter(
                addons__contains=addon_type
            ).count() / similar_positions.count() if similar_positions.exists() else 0
            
            # Recomendar si la tasa de uso es alta
            if usage_rate > 0.5:
                addon_recommendations.append({
                    'type': addon_type,
                    'usage_rate': usage_rate,
                    'recommended': True
                })
        
        return addon_recommendations 