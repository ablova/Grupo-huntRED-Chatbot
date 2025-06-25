"""
Dashboard específico para Clientes con funcionalidades limitadas y controladas.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class ClientDashboard:
    """
    Dashboard controlado para clientes con acceso limitado a sus procesos.
    """
    
    def __init__(self, client_id: int):
        self.client_id = client_id
        self.client_name = self._get_client_name()
        self.client_type = self._get_client_type()
        self.consultant_assigned = self._get_consultant_assigned()
    
    def _get_client_name(self) -> str:
        """Obtiene el nombre del cliente."""
        # Simulación - en producción vendría de la base de datos
        return "TechCorp Solutions"
    
    def _get_client_type(self) -> str:
        """Obtiene el tipo de cliente."""
        # Simulación - en producción vendría de la base de datos
        return "Enterprise"
    
    def _get_consultant_assigned(self) -> str:
        """Obtiene el consultor asignado al cliente."""
        # Simulación - en producción vendría de la base de datos
        return "María Rodríguez"
    
    def get_client_kanban_data(self, filters: Dict = None) -> Dict:
        """
        Kanban simplificado para clientes - solo sus candidatos.
        """
        try:
            if not filters:
                filters = {
                    'period': 'month',
                    'status': 'all',
                    'position': 'all'
                }
            
            kanban_data = {
                'client_info': {
                    'id': self.client_id,
                    'name': self.client_name,
                    'type': self.client_type,
                    'consultant': self.consultant_assigned
                },
                'filters': filters,
                'columns': self._get_client_kanban_columns(),
                'candidates': self._get_client_candidates(filters),
                'metrics': self._get_client_metrics(filters)
            }
            
            return kanban_data
            
        except Exception as e:
            logger.error(f"Error en kanban de cliente: {str(e)}")
            return {'error': str(e)}
    
    def _get_client_kanban_columns(self) -> Dict:
        """Columnas del kanban para clientes (solo lectura)."""
        return {
            'sourcing': {
                'title': 'En Búsqueda',
                'icon': 'fas fa-search',
                'color': '#17a2b8',
                'count': 0,
                'readonly': True
            },
            'screening': {
                'title': 'En Evaluación',
                'icon': 'fas fa-filter',
                'color': '#ffc107',
                'count': 0,
                'readonly': True
            },
            'interviewing': {
                'title': 'En Entrevista',
                'icon': 'fas fa-comments',
                'color': '#007bff',
                'count': 0,
                'readonly': True
            },
            'references': {
                'title': 'Verificando Referencias',
                'icon': 'fas fa-phone',
                'color': '#6f42c1',
                'count': 0,
                'readonly': True
            },
            'offer': {
                'title': 'Propuesta Enviada',
                'icon': 'fas fa-file-contract',
                'color': '#fd7e14',
                'count': 0,
                'readonly': True
            },
            'hired': {
                'title': 'Contratado',
                'icon': 'fas fa-check-circle',
                'color': '#28a745',
                'count': 0,
                'readonly': True
            }
        }
    
    def _get_client_candidates(self, filters: Dict) -> Dict:
        """Candidatos del cliente (solo información básica)."""
        # Simulación de candidatos del cliente
        candidates_data = {
            'sourcing': [
                {
                    'id': 1,
                    'name': 'Ana García López',
                    'position': 'Senior Developer',
                    'location': 'CDMX',
                    'experience': '5 años',
                    'status': 'sourcing',
                    'priority': 'high',
                    'last_activity': '2024-01-15',
                    'match_score': 85,
                    'availability': 'Inmediata',
                    'consultant_notes': 'Candidata con experiencia en React y Node.js',
                    'client_notes': '',  # Cliente puede agregar notas
                    'cv_available': True,
                    'cv_download_url': '/client/cv/download/1/'
                }
            ],
            'interviewing': [
                {
                    'id': 4,
                    'name': 'Fernando Morales',
                    'position': 'Data Scientist',
                    'location': 'CDMX',
                    'experience': '4 años',
                    'status': 'interviewing',
                    'priority': 'high',
                    'last_activity': '2024-01-17',
                    'match_score': 88,
                    'availability': 'Inmediata',
                    'interview_schedule': {
                        'next_interview': '2024-01-18 14:00',
                        'interviewer': 'Dr. Carlos Ruiz',
                        'type': 'Técnica'
                    },
                    'client_notes': 'Excelente candidato, muy interesado en el proyecto',
                    'cv_available': True,
                    'cv_download_url': '/client/cv/download/4/'
                }
            ],
            'offer': [
                {
                    'id': 6,
                    'name': 'Miguel Ángel Ruiz',
                    'position': 'DevOps Engineer',
                    'location': 'Querétaro',
                    'experience': '5 años',
                    'status': 'offer',
                    'priority': 'high',
                    'last_activity': '2024-01-17',
                    'match_score': 90,
                    'availability': 'Inmediata',
                    'offer_details': {
                        'salary_offered': '$88,000 MXN',
                        'offer_date': '2024-01-17',
                        'response_deadline': '2024-01-24',
                        'status': 'Pending'
                    },
                    'client_notes': 'Candidato ideal para el equipo',
                    'cv_available': True,
                    'cv_download_url': '/client/cv/download/6/'
                }
            ],
            'hired': [
                {
                    'id': 7,
                    'name': 'Valeria Castro',
                    'position': 'Frontend Developer',
                    'location': 'CDMX',
                    'experience': '3 años',
                    'status': 'hired',
                    'priority': 'medium',
                    'last_activity': '2024-01-10',
                    'match_score': 85,
                    'availability': 'Contratada',
                    'hiring_details': {
                        'hire_date': '2024-01-10',
                        'start_date': '2024-02-01',
                        'salary_final': '$72,000 MXN',
                        'contract_type': 'Indefinido'
                    },
                    'client_notes': 'Excelente contratación, se integró perfectamente',
                    'cv_available': True,
                    'cv_download_url': '/client/cv/download/7/'
                }
            ]
        }
        
        # Actualizar conteos
        for status, candidates in candidates_data.items():
            if status in self._get_client_kanban_columns():
                self._get_client_kanban_columns()[status]['count'] = len(candidates)
        
        return candidates_data
    
    def _get_client_metrics(self, filters: Dict) -> Dict:
        """Métricas del cliente (limitadas)."""
        return {
            'total_candidates': 15,
            'active_candidates': 12,
            'hired_this_period': 2,
            'avg_time_to_hire': '25 días',
            'satisfaction_score': 4.8,
            'active_positions': 3,
            'by_status': {
                'sourcing': 5,
                'screening': 3,
                'interviewing': 2,
                'references': 1,
                'offer': 1,
                'hired': 2
            },
            'by_position': {
                'Senior Developer': 6,
                'Data Scientist': 4,
                'DevOps Engineer': 3,
                'Frontend Developer': 2
            }
        }
    
    def get_client_cv_data(self, candidate_id: int) -> Dict:
        """
        Datos de CV para cliente (muy limitado).
        """
        try:
            # Verificar que el candidato pertenece al cliente
            if not self._candidate_belongs_to_client(candidate_id):
                return {'error': 'Acceso denegado'}
            
            cv_data = {
                'candidate_id': candidate_id,
                'candidate_name': 'Ana García López',
                'position': 'Senior Developer',
                'cv_url': '/media/cvs/ana_garcia_cv.pdf',
                'cv_preview_url': '/media/cvs/ana_garcia_cv_preview.html',
                'cv_created_date': '2024-01-15',
                'cv_version': '2.1',
                'cv_status': 'active',
                'cv_views': {
                    'candidate': False,  # Cliente no puede ver
                    'client': True,
                    'consultant': False,  # Cliente no puede ver
                    'super_admin': False  # Cliente no puede ver
                },
                'export_options': {
                    'pdf': True,
                    'docx': False,  # Limitado
                    'html': False,  # Limitado
                    'txt': False    # Limitado
                },
                'cv_analytics': {
                    'total_views': 12,
                    'views_by_role': {
                        'client': 12
                    },
                    'downloads': 2,
                    'last_viewed': '2024-01-17 14:30'
                },
                'permissions': {
                    'can_download': True,
                    'can_share': False,  # Limitado
                    'can_edit': False,   # Limitado
                    'can_delete': False  # Limitado
                }
            }
            
            return cv_data
            
        except Exception as e:
            logger.error(f"Error en CV de cliente: {str(e)}")
            return {'error': str(e)}
    
    def get_client_reports_data(self, filters: Dict = None) -> Dict:
        """
        Reportes del cliente (muy limitados).
        """
        try:
            if not filters:
                filters = {
                    'period': 'month',
                    'report_type': 'process'
                }
            
            reports_data = {
                'client_info': {
                    'id': self.client_id,
                    'name': self.client_name,
                    'type': self.client_type,
                    'consultant': self.consultant_assigned
                },
                'filters': filters,
                'report_types': [
                    {
                        'id': 'process',
                        'name': 'Mis Procesos',
                        'description': 'Estado de procesos de contratación',
                        'icon': 'fas fa-tasks'
                    },
                    {
                        'id': 'candidates',
                        'name': 'Mis Candidatos',
                        'description': 'Análisis de candidatos en proceso',
                        'icon': 'fas fa-users'
                    },
                    {
                        'id': 'satisfaction',
                        'name': 'Satisfacción',
                        'description': 'Métricas de satisfacción del servicio',
                        'icon': 'fas fa-star'
                    }
                ],
                'process_report': {
                    'summary': {
                        'active_processes': 3,
                        'total_candidates': 15,
                        'hires_this_period': 2,
                        'avg_time_to_hire': '25 días',
                        'satisfaction_score': 4.8
                    },
                    'processes': [
                        {
                            'position': 'Senior Developer',
                            'candidates': 6,
                            'status': 'Active',
                            'start_date': '2024-01-01',
                            'expected_completion': '2024-02-15'
                        },
                        {
                            'position': 'Data Scientist',
                            'candidates': 4,
                            'status': 'Active',
                            'start_date': '2024-01-10',
                            'expected_completion': '2024-02-20'
                        },
                        {
                            'position': 'DevOps Engineer',
                            'candidates': 3,
                            'status': 'Active',
                            'start_date': '2024-01-15',
                            'expected_completion': '2024-02-25'
                        }
                    ]
                },
                'candidates_report': {
                    'by_status': {
                        'sourcing': 5,
                        'screening': 3,
                        'interviewing': 2,
                        'references': 1,
                        'offer': 1,
                        'hired': 2
                    },
                    'by_position': {
                        'Senior Developer': 6,
                        'Data Scientist': 4,
                        'DevOps Engineer': 3,
                        'Frontend Developer': 2
                    },
                    'by_location': {
                        'CDMX': 10,
                        'Querétaro': 3,
                        'Guadalajara': 2
                    }
                },
                'satisfaction_report': {
                    'overall_satisfaction': 4.8,
                    'service_quality': 4.9,
                    'communication': 4.7,
                    'timeline_adherence': 4.6,
                    'candidate_quality': 4.8,
                    'feedback_history': [
                        {
                            'date': '2024-01-15',
                            'rating': 5.0,
                            'comment': 'Excelente servicio, candidatos de alta calidad'
                        },
                        {
                            'date': '2024-01-10',
                            'rating': 4.5,
                            'comment': 'Buen proceso, comunicación clara'
                        }
                    ]
                },
                'export_options': {
                    'formats': ['pdf'],  # Solo PDF
                    'scheduling': False,  # Limitado
                    'automated_delivery': False,  # Limitado
                    'customization': False  # Limitado
                }
            }
            
            return reports_data
            
        except Exception as e:
            logger.error(f"Error en reportes de cliente: {str(e)}")
            return {'error': str(e)}
    
    def _candidate_belongs_to_client(self, candidate_id: int) -> bool:
        """Verifica si el candidato pertenece al cliente."""
        # Simulación - en producción verificaría en la base de datos
        client_candidates = [1, 4, 6, 7, 9, 12, 15]  # IDs de candidatos del cliente
        return candidate_id in client_candidates
    
    def get_client_dashboard_summary(self) -> Dict:
        """
        Resumen del dashboard para cliente.
        """
        try:
            return {
                'client_info': {
                    'id': self.client_id,
                    'name': self.client_name,
                    'type': self.client_type,
                    'consultant': self.consultant_assigned,
                    'role': 'Cliente',
                    'access_level': 'Limited'
                },
                'quick_stats': {
                    'active_candidates': 12,
                    'interviews_scheduled': 2,
                    'offers_pending': 1,
                    'hires_this_month': 2
                },
                'recent_activities': [
                    {
                        'date': '2024-01-17',
                        'action': 'Nueva candidata agregada: Ana García López',
                        'type': 'candidate'
                    },
                    {
                        'date': '2024-01-16',
                        'action': 'Entrevista programada con Fernando Morales',
                        'type': 'interview'
                    },
                    {
                        'date': '2024-01-15',
                        'action': 'Propuesta enviada a Miguel Ángel Ruiz',
                        'type': 'offer'
                    }
                ],
                'upcoming_events': [
                    {
                        'date': '2024-01-18',
                        'event': 'Entrevista técnica con Fernando Morales',
                        'type': 'interview'
                    },
                    {
                        'date': '2024-01-19',
                        'event': 'Seguimiento de propuesta Miguel Ángel Ruiz',
                        'type': 'follow_up'
                    },
                    {
                        'date': '2024-01-20',
                        'event': 'Reunión de seguimiento con consultor',
                        'type': 'meeting'
                    }
                ],
                'consultant_contact': {
                    'name': self.consultant_assigned,
                    'email': 'maria.rodriguez@huntred.com',
                    'phone': '+52 55 1234 5678',
                    'availability': 'Lun-Vie 9:00-18:00'
                }
            }
            
        except Exception as e:
            logger.error(f"Error en resumen de dashboard: {str(e)}")
            return {'error': str(e)}
    
    def add_client_note(self, candidate_id: int, note: str) -> Dict:
        """
        Permite al cliente agregar notas a sus candidatos.
        """
        try:
            if not self._candidate_belongs_to_client(candidate_id):
                return {'error': 'Acceso denegado'}
            
            # Simulación de guardado de nota
            note_data = {
                'candidate_id': candidate_id,
                'note': note,
                'client_id': self.client_id,
                'created_at': datetime.now().isoformat(),
                'status': 'saved'
            }
            
            return {
                'success': True,
                'message': 'Nota agregada exitosamente',
                'note_data': note_data
            }
            
        except Exception as e:
            logger.error(f"Error agregando nota de cliente: {str(e)}")
            return {'error': str(e)}
    
    def request_cv_download(self, candidate_id: int) -> Dict:
        """
        Solicita descarga de CV (con registro).
        """
        try:
            if not self._candidate_belongs_to_client(candidate_id):
                return {'error': 'Acceso denegado'}
            
            # Simulación de registro de descarga
            download_data = {
                'candidate_id': candidate_id,
                'client_id': self.client_id,
                'download_date': datetime.now().isoformat(),
                'cv_url': f'/media/cvs/candidate_{candidate_id}_cv.pdf'
            }
            
            return {
                'success': True,
                'message': 'CV disponible para descarga',
                'download_data': download_data
            }
            
        except Exception as e:
            logger.error(f"Error en descarga de CV: {str(e)}")
            return {'error': str(e)} 