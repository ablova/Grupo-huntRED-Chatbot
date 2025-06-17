"""
Sistema de logging para rankings educativos.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os
from pathlib import Path

class RankingLogger:
    """Sistema de logging para rankings educativos."""
    
    def __init__(self,
                 log_dir: str = 'logs',
                 log_level: int = logging.INFO):
        """
        Inicializa el sistema de logging.
        
        Args:
            log_dir: Directorio para logs
            log_level: Nivel de logging
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar logger principal
        self.logger = logging.getLogger('ranking_system')
        self.logger.setLevel(log_level)
        
        # Handler para archivo
        log_file = self.log_dir / f'rankings_{datetime.now().strftime("%Y%m%d")}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        
        # Formato
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Agregar handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Loggers específicos
        self.ranking_logger = logging.getLogger('ranking_system.rankings')
        self.cache_logger = logging.getLogger('ranking_system.cache')
        self.ml_logger = logging.getLogger('ranking_system.ml')
        
        # Configurar loggers específicos
        for logger in [self.ranking_logger, self.cache_logger, self.ml_logger]:
            logger.setLevel(log_level)
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
            
    def log_ranking_update(self,
                          university: str,
                          ranking: int,
                          source: str,
                          program: Optional[str] = None,
                          metrics: Optional[Dict[str, Any]] = None) -> None:
        """
        Registra una actualización de ranking.
        
        Args:
            university: Nombre de la universidad
            ranking: Nuevo ranking
            source: Fuente del ranking
            program: Nombre del programa (opcional)
            metrics: Métricas adicionales (opcional)
        """
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'university': university,
            'ranking': ranking,
            'source': source,
            'program': program,
            'metrics': metrics
        }
        
        self.ranking_logger.info(
            f"Ranking actualizado: {json.dumps(log_data)}"
        )
        
    def log_cache_operation(self,
                           operation: str,
                           key: str,
                           success: bool,
                           error: Optional[str] = None) -> None:
        """
        Registra una operación de caché.
        
        Args:
            operation: Tipo de operación ('get', 'set', 'delete')
            key: Clave de caché
            success: Si la operación fue exitosa
            error: Mensaje de error (opcional)
        """
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'key': key,
            'success': success,
            'error': error
        }
        
        self.cache_logger.info(
            f"Operación de caché: {json.dumps(log_data)}"
        )
        
    def log_ml_prediction(self,
                         model: str,
                         input_data: Dict[str, Any],
                         prediction: float,
                         confidence: float) -> None:
        """
        Registra una predicción de ML.
        
        Args:
            model: Nombre del modelo
            input_data: Datos de entrada
            prediction: Predicción
            confidence: Nivel de confianza
        """
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'model': model,
            'input_data': input_data,
            'prediction': prediction,
            'confidence': confidence
        }
        
        self.ml_logger.info(
            f"Predicción ML: {json.dumps(log_data)}"
        )
        
    def log_error(self,
                 error_type: str,
                 message: str,
                 details: Optional[Dict[str, Any]] = None) -> None:
        """
        Registra un error.
        
        Args:
            error_type: Tipo de error
            message: Mensaje de error
            details: Detalles adicionales (opcional)
        """
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'message': message,
            'details': details
        }
        
        self.logger.error(
            f"Error: {json.dumps(log_data)}"
        )
        
    def log_performance_metrics(self,
                              metrics: Dict[str, float]) -> None:
        """
        Registra métricas de rendimiento.
        
        Args:
            metrics: Diccionario con métricas
        """
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics
        }
        
        self.logger.info(
            f"Métricas de rendimiento: {json.dumps(log_data)}"
        )
        
    def get_recent_logs(self,
                       n: int = 100,
                       log_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtiene logs recientes.
        
        Args:
            n: Número de logs a retornar
            log_type: Tipo de log ('rankings', 'cache', 'ml')
            
        Returns:
            Lista de logs
        """
        log_file = self.log_dir / f'rankings_{datetime.now().strftime("%Y%m%d")}.log'
        
        if not log_file.exists():
            return []
            
        logs = []
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    # Parsear línea de log
                    parts = line.split(' - ')
                    if len(parts) < 4:
                        continue
                        
                    timestamp = parts[0]
                    name = parts[1]
                    level = parts[2]
                    message = ' - '.join(parts[3:])
                    
                    # Filtrar por tipo si se especifica
                    if log_type and log_type not in name:
                        continue
                        
                    # Parsear mensaje JSON si existe
                    try:
                        message_data = json.loads(message.split(': ')[1])
                    except:
                        message_data = {'message': message}
                        
                    logs.append({
                        'timestamp': timestamp,
                        'name': name,
                        'level': level,
                        'data': message_data
                    })
                except:
                    continue
                    
        # Ordenar por timestamp y limitar
        logs.sort(key=lambda x: x['timestamp'], reverse=True)
        return logs[:n]
        
    def analyze_logs(self,
                    start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Analiza logs en un rango de fechas.
        
        Args:
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)
            
        Returns:
            Estadísticas de logs
        """
        stats = {
            'total_logs': 0,
            'error_count': 0,
            'ranking_updates': 0,
            'cache_operations': 0,
            'ml_predictions': 0,
            'performance_metrics': []
        }
        
        # Obtener logs recientes
        logs = self.get_recent_logs(n=1000)
        
        for log in logs:
            # Filtrar por fecha si se especifica
            log_date = datetime.fromisoformat(log['timestamp'])
            if start_date and log_date < start_date:
                continue
            if end_date and log_date > end_date:
                continue
                
            stats['total_logs'] += 1
            
            # Contar por tipo
            if 'ERROR' in log['level']:
                stats['error_count'] += 1
            elif 'rankings' in log['name']:
                stats['ranking_updates'] += 1
            elif 'cache' in log['name']:
                stats['cache_operations'] += 1
            elif 'ml' in log['name']:
                stats['ml_predictions'] += 1
                
            # Recolectar métricas de rendimiento
            if 'Métricas de rendimiento' in log['data'].get('message', ''):
                stats['performance_metrics'].append(
                    log['data'].get('metrics', {})
                )
                
        return stats 