"""
Sistema de Analytics de Costos y Operaciones por Proceso.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class CostAnalyticsSystem:
    """
    Sistema avanzado de analytics de costos y operaciones.
    """
    
    def __init__(self):
        self.cost_data = {}
        self.operation_metrics = {}
        self.server_costs = self._get_server_costs()
        self.message_costs = self._get_message_costs()
    
    def _get_server_costs(self) -> Dict:
        """Obtiene costos de servidores por mes."""
        return {
            'aws_ec2': 1200,  # USD por mes
            'aws_rds': 800,   # USD por mes
            'aws_s3': 200,    # USD por mes
            'aws_lambda': 150, # USD por mes
            'cloudflare': 100, # USD por mes
            'total_monthly': 2450
        }
    
    def _get_message_costs(self) -> Dict:
        """Obtiene costos por tipo de mensaje."""
        return {
            'email': 0.001,      # USD por email
            'sms': 0.05,         # USD por SMS
            'whatsapp': 0.02,    # USD por mensaje WhatsApp
            'linkedin': 0.10,    # USD por mensaje LinkedIn
            'slack': 0.001,      # USD por mensaje Slack
            'aura_chat': 0.005   # USD por mensaje AURA
        }
    
    def track_process_costs(self, process_id: int, action: str, cost_data: Dict):
        """
        Registra costos de un proceso específico.
        """
        try:
            if process_id not in self.cost_data:
                self.cost_data[process_id] = {
                    'total_cost': 0.0,
                    'actions': [],
                    'messages': [],
                    'server_usage': [],
                    'start_date': datetime.now().isoformat(),
                    'last_updated': datetime.now().isoformat()
                }
            
            # Registrar acción
            action_record = {
                'timestamp': datetime.now().isoformat(),
                'action': action,
                'cost': cost_data.get('cost', 0.0),
                'details': cost_data.get('details', {})
            }
            
            self.cost_data[process_id]['actions'].append(action_record)
            self.cost_data[process_id]['total_cost'] += cost_data.get('cost', 0.0)
            self.cost_data[process_id]['last_updated'] = datetime.now().isoformat()
            
            logger.info(f"Costos registrados para proceso {process_id}: {action} - ${cost_data.get('cost', 0.0)}")
            
        except Exception as e:
            logger.error(f"Error registrando costos: {str(e)}")
    
    def track_message_costs(self, process_id: int, message_type: str, count: int = 1):
        """
        Registra costos de mensajes por proceso.
        """
        try:
            if process_id not in self.cost_data:
                self.cost_data[process_id] = {
                    'total_cost': 0.0,
                    'actions': [],
                    'messages': [],
                    'server_usage': [],
                    'start_date': datetime.now().isoformat(),
                    'last_updated': datetime.now().isoformat()
                }
            
            message_cost = self.message_costs.get(message_type, 0.0) * count
            
            message_record = {
                'timestamp': datetime.now().isoformat(),
                'type': message_type,
                'count': count,
                'unit_cost': self.message_costs.get(message_type, 0.0),
                'total_cost': message_cost
            }
            
            self.cost_data[process_id]['messages'].append(message_record)
            self.cost_data[process_id]['total_cost'] += message_cost
            self.cost_data[process_id]['last_updated'] = datetime.now().isoformat()
            
            logger.info(f"Mensajes registrados para proceso {process_id}: {message_type} x{count} - ${message_cost}")
            
        except Exception as e:
            logger.error(f"Error registrando mensajes: {str(e)}")
    
    def track_server_usage(self, process_id: int, service: str, usage_hours: float = 1.0):
        """
        Registra uso de servidores por proceso.
        """
        try:
            if process_id not in self.cost_data:
                self.cost_data[process_id] = {
                    'total_cost': 0.0,
                    'actions': [],
                    'messages': [],
                    'server_usage': [],
                    'start_date': datetime.now().isoformat(),
                    'last_updated': datetime.now().isoformat()
                }
            
            # Calcular costo por hora
            monthly_cost = self.server_costs.get(service, 0.0)
            hourly_cost = monthly_cost / (30 * 24)  # Asumiendo 30 días por mes
            usage_cost = hourly_cost * usage_hours
            
            usage_record = {
                'timestamp': datetime.now().isoformat(),
                'service': service,
                'usage_hours': usage_hours,
                'hourly_cost': hourly_cost,
                'total_cost': usage_cost
            }
            
            self.cost_data[process_id]['server_usage'].append(usage_record)
            self.cost_data[process_id]['total_cost'] += usage_cost
            self.cost_data[process_id]['last_updated'] = datetime.now().isoformat()
            
            logger.info(f"Uso de servidor registrado para proceso {process_id}: {service} - {usage_hours}h - ${usage_cost}")
            
        except Exception as e:
            logger.error(f"Error registrando uso de servidor: {str(e)}")
    
    def get_process_cost_analysis(self, process_id: int) -> Dict:
        """
        Obtiene análisis completo de costos de un proceso.
        """
        try:
            if process_id not in self.cost_data:
                return {'error': 'Proceso no encontrado'}
            
            process_data = self.cost_data[process_id]
            
            # Análisis de costos por categoría
            message_costs = sum(msg['total_cost'] for msg in process_data['messages'])
            server_costs = sum(usage['total_cost'] for usage in process_data['server_usage'])
            action_costs = sum(action['cost'] for action in process_data['actions'])
            
            # Análisis de mensajes por tipo
            message_breakdown = {}
            for msg in process_data['messages']:
                msg_type = msg['type']
                if msg_type not in message_breakdown:
                    message_breakdown[msg_type] = {
                        'count': 0,
                        'total_cost': 0.0
                    }
                message_breakdown[msg_type]['count'] += msg['count']
                message_breakdown[msg_type]['total_cost'] += msg['total_cost']
            
            # Análisis de uso de servidores
            server_breakdown = {}
            for usage in process_data['server_usage']:
                service = usage['service']
                if service not in server_breakdown:
                    server_breakdown[service] = {
                        'total_hours': 0.0,
                        'total_cost': 0.0
                    }
                server_breakdown[service]['total_hours'] += usage['usage_hours']
                server_breakdown[service]['total_cost'] += usage['total_cost']
            
            # Calcular métricas de tiempo
            start_date = datetime.fromisoformat(process_data['start_date'])
            last_updated = datetime.fromisoformat(process_data['last_updated'])
            duration_days = (last_updated - start_date).days
            
            return {
                'process_id': process_id,
                'total_cost': process_data['total_cost'],
                'duration_days': duration_days,
                'cost_per_day': process_data['total_cost'] / max(duration_days, 1),
                'cost_breakdown': {
                    'messages': message_costs,
                    'server_usage': server_costs,
                    'actions': action_costs
                },
                'message_breakdown': message_breakdown,
                'server_breakdown': server_breakdown,
                'actions_count': len(process_data['actions']),
                'messages_count': sum(msg['count'] for msg in process_data['messages']),
                'start_date': process_data['start_date'],
                'last_updated': process_data['last_updated']
            }
            
        except Exception as e:
            logger.error(f"Error analizando costos: {str(e)}")
            return {'error': str(e)}
    
    def get_all_processes_cost_summary(self) -> Dict:
        """
        Obtiene resumen de costos de todos los procesos.
        """
        try:
            if not self.cost_data:
                return {'error': 'No hay datos de costos'}
            
            total_cost = sum(process['total_cost'] for process in self.cost_data.values())
            total_processes = len(self.cost_data)
            
            # Análisis por categoría
            total_message_costs = 0
            total_server_costs = 0
            total_action_costs = 0
            
            message_types = {}
            server_services = {}
            
            for process_data in self.cost_data.values():
                # Mensajes
                for msg in process_data['messages']:
                    msg_type = msg['type']
                    if msg_type not in message_types:
                        message_types[msg_type] = {'count': 0, 'cost': 0.0}
                    message_types[msg_type]['count'] += msg['count']
                    message_types[msg_type]['cost'] += msg['total_cost']
                    total_message_costs += msg['total_cost']
                
                # Servidores
                for usage in process_data['server_usage']:
                    service = usage['service']
                    if service not in server_services:
                        server_services[service] = {'hours': 0.0, 'cost': 0.0}
                    server_services[service]['hours'] += usage['usage_hours']
                    server_services[service]['cost'] += usage['total_cost']
                    total_server_costs += usage['total_cost']
                
                # Acciones
                for action in process_data['actions']:
                    total_action_costs += action['cost']
            
            return {
                'summary': {
                    'total_cost': total_cost,
                    'total_processes': total_processes,
                    'average_cost_per_process': total_cost / total_processes if total_processes > 0 else 0,
                    'cost_breakdown': {
                        'messages': total_message_costs,
                        'server_usage': total_server_costs,
                        'actions': total_action_costs
                    }
                },
                'message_analysis': message_types,
                'server_analysis': server_services,
                'processes': list(self.cost_data.keys())
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen: {str(e)}")
            return {'error': str(e)}
    
    def calculate_roi_per_process(self, process_id: int, revenue: float) -> Dict:
        """
        Calcula ROI de un proceso específico.
        """
        try:
            if process_id not in self.cost_data:
                return {'error': 'Proceso no encontrado'}
            
            total_cost = self.cost_data[process_id]['total_cost']
            
            if total_cost == 0:
                return {'error': 'No hay costos registrados'}
            
            roi = ((revenue - total_cost) / total_cost) * 100
            profit_margin = ((revenue - total_cost) / revenue) * 100 if revenue > 0 else 0
            
            return {
                'process_id': process_id,
                'total_cost': total_cost,
                'revenue': revenue,
                'roi_percentage': roi,
                'profit_margin_percentage': profit_margin,
                'net_profit': revenue - total_cost
            }
            
        except Exception as e:
            logger.error(f"Error calculando ROI: {str(e)}")
            return {'error': str(e)}
    
    def get_cost_optimization_recommendations(self) -> List[Dict]:
        """
        Genera recomendaciones de optimización de costos.
        """
        try:
            recommendations = []
            
            # Analizar patrones de uso
            all_message_costs = {}
            all_server_costs = {}
            
            for process_data in self.cost_data.values():
                for msg in process_data['messages']:
                    msg_type = msg['type']
                    if msg_type not in all_message_costs:
                        all_message_costs[msg_type] = 0.0
                    all_message_costs[msg_type] += msg['total_cost']
                
                for usage in process_data['server_usage']:
                    service = usage['service']
                    if service not in all_server_costs:
                        all_server_costs[service] = 0.0
                    all_server_costs[service] += usage['total_cost']
            
            # Recomendaciones de mensajes
            if all_message_costs.get('sms', 0) > all_message_costs.get('whatsapp', 0) * 2:
                recommendations.append({
                    'type': 'message_optimization',
                    'title': 'Migrar de SMS a WhatsApp',
                    'description': 'WhatsApp es 60% más económico que SMS',
                    'potential_savings': all_message_costs.get('sms', 0) * 0.6,
                    'priority': 'high'
                })
            
            # Recomendaciones de servidores
            if all_server_costs.get('aws_ec2', 0) > 1000:
                recommendations.append({
                    'type': 'server_optimization',
                    'title': 'Optimizar uso de EC2',
                    'description': 'Considerar instancias reservadas o auto-scaling',
                    'potential_savings': all_server_costs.get('aws_ec2', 0) * 0.3,
                    'priority': 'medium'
                })
            
            # Recomendaciones generales
            total_cost = sum(process['total_cost'] for process in self.cost_data.values())
            if total_cost > 5000:
                recommendations.append({
                    'type': 'general_optimization',
                    'title': 'Revisar procesos de alto costo',
                    'description': 'Identificar y optimizar procesos con costos superiores a $500',
                    'potential_savings': total_cost * 0.15,
                    'priority': 'high'
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generando recomendaciones: {str(e)}")
            return []
    
    def export_cost_report(self, format: str = 'json') -> str:
        """
        Exporta reporte de costos en diferentes formatos.
        """
        try:
            report_data = {
                'timestamp': datetime.now().isoformat(),
                'summary': self.get_all_processes_cost_summary(),
                'process_details': {
                    process_id: self.get_process_cost_analysis(process_id)
                    for process_id in self.cost_data.keys()
                },
                'recommendations': self.get_cost_optimization_recommendations()
            }
            
            if format == 'json':
                return json.dumps(report_data, indent=2)
            elif format == 'csv':
                # Convertir a CSV
                df = pd.DataFrame([
                    {
                        'process_id': process_id,
                        'total_cost': data['total_cost'],
                        'duration_days': data['duration_days'],
                        'cost_per_day': data['cost_per_day']
                    }
                    for process_id, data in report_data['process_details'].items()
                    if 'error' not in data
                ])
                return df.to_csv(index=False)
            else:
                return json.dumps(report_data, indent=2)
                
        except Exception as e:
            logger.error(f"Error exportando reporte: {str(e)}")
            return json.dumps({'error': str(e)})
    
    def get_pricing_recommendations(self, target_margin: float = 0.3) -> Dict:
        """
        Genera recomendaciones de pricing basadas en costos.
        """
        try:
            total_cost = sum(process['total_cost'] for process in self.cost_data.values())
            total_processes = len(self.cost_data)
            
            if total_processes == 0:
                return {'error': 'No hay datos suficientes'}
            
            average_cost_per_process = total_cost / total_processes
            
            # Calcular precio recomendado
            recommended_price = average_cost_per_process / (1 - target_margin)
            
            # Análisis por tipo de proceso
            process_types = {}
            for process_id, process_data in self.cost_data.items():
                # Simular tipo de proceso basado en costos
                if process_data['total_cost'] > 1000:
                    process_type = 'executive'
                elif process_data['total_cost'] > 500:
                    process_type = 'senior'
                else:
                    process_type = 'junior'
                
                if process_type not in process_types:
                    process_types[process_type] = {'count': 0, 'total_cost': 0.0}
                
                process_types[process_type]['count'] += 1
                process_types[process_type]['total_cost'] += process_data['total_cost']
            
            # Precios recomendados por tipo
            pricing_by_type = {}
            for process_type, data in process_types.items():
                avg_cost = data['total_cost'] / data['count']
                recommended_price_type = avg_cost / (1 - target_margin)
                pricing_by_type[process_type] = {
                    'average_cost': avg_cost,
                    'recommended_price': recommended_price_type,
                    'margin': target_margin * 100
                }
            
            return {
                'overall_recommendations': {
                    'average_cost_per_process': average_cost_per_process,
                    'recommended_price': recommended_price,
                    'target_margin_percentage': target_margin * 100,
                    'total_processes_analyzed': total_processes
                },
                'pricing_by_type': pricing_by_type,
                'cost_breakdown': {
                    'total_cost': total_cost,
                    'average_cost': average_cost_per_process,
                    'cost_variance': np.std([p['total_cost'] for p in self.cost_data.values()])
                }
            }
            
        except Exception as e:
            logger.error(f"Error generando recomendaciones de pricing: {str(e)}")
            return {'error': str(e)} 