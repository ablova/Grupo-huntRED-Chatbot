from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from ..utils.visualization.report_generator import ReportGenerator
import logging

logger = logging.getLogger('app.com.views.visualization')

class VisualizationView:
    """Vistas para la visualización del flujo de comunicaciones."""
    
    @staticmethod
    @api_view(['GET'])
    def get_conversation_metrics(request):
        """Obtiene métricas de conversaciones."""
        try:
            generator = ReportGenerator()
            metrics = generator.generate_conversation_metrics()
            return Response(metrics, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error getting conversation metrics: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @staticmethod
    @api_view(['GET'])
    def get_message_metrics(request):
        """Obtiene métricas de mensajes."""
        try:
            generator = ReportGenerator()
            metrics = generator.generate_message_metrics()
            return Response(metrics, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error getting message metrics: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @staticmethod
    @api_view(['GET'])
    def get_notification_metrics(request):
        """Obtiene métricas de notificaciones."""
        try:
            generator = ReportGenerator()
            metrics = generator.generate_notification_metrics()
            return Response(metrics, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error getting notification metrics: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @staticmethod
    @api_view(['GET'])
    def get_workflow_metrics(request):
        """Obtiene métricas del flujo de trabajo."""
        try:
            generator = ReportGenerator()
            metrics = generator.generate_workflow_metrics()
            return Response(metrics, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error getting workflow metrics: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @staticmethod
    @api_view(['GET'])
    def get_comprehensive_report(request):
        """Obtiene un reporte completo de todas las métricas."""
        try:
            generator = ReportGenerator()
            report = generator.generate_comprehensive_report()
            return Response(report, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error getting comprehensive report: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @staticmethod
    def dashboard(request):
        """Muestra el dashboard de visualización."""
        return render(request, 'com/visualization/dashboard.html')
