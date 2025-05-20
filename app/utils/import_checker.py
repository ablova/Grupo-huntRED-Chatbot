#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# /home/pablo/app/utils/import_checker.py
#
# Utilidad para verificar y corregir problemas de importación circular
# Siguiendo las reglas globales de Grupo huntRED®:
# - No Redundancies: Verificar antes de añadir funciones que no existan en el código
# - Modularity: Escribir código modular, reutilizable; evitar duplicar funcionalidad
# - Code Consistency: Seguir estándares de Django
#

import os
import re
import ast
import logging
import importlib
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional
import networkx as nx
from collections import defaultdict

# Configuración del logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('import_checker')

class ImportAnalyzer:
    """Analizador de importaciones para detectar y corregir problemas.
    
    Esta clase contiene utilidades para:
    1. Detectar importaciones circulares
    2. Identificar patrones de importación problemáticos
    3. Sugerir correcciones basadas en buenas prácticas
    """
    
    def __init__(self, base_path: str = None):
        """Inicializa el analizador de importaciones.
        
        Args:
            base_path: Ruta base del proyecto a analizar. Si es None, se usa el directorio actual.
        """
        self.base_path = Path(base_path) if base_path else Path(os.getcwd())
        self.import_graph = nx.DiGraph()
        self.problematic_patterns = [
            r'from \.(?!models|forms|views|signals)([^ ]+) import',  # Importaciones relativas problemáticas
            r'from app\.import_config import (get_\w+)',  # Funciones getter del import_config
            r'from app\.(com|ml|pagos|publish|sexsi|utilidades)\.import_config import',  # Import_config de submódulos
        ]
        self.ignore_dirs = {'__pycache__', 'migrations', '.git', '.idea', '.vscode', 'venv'}
        self.ignore_files = {'__init__.py', 'settings.py', 'apps.py'}
        
    def scan_project(self) -> None:
        """Escanea todo el proyecto para construir el grafo de importaciones."""
        logger.info(f"Escaneando proyecto en {self.base_path}")
        for file_path in self._get_python_files():
            self._analyze_file(file_path)
        
        logger.info(f"Grafo de importaciones construido con {len(self.import_graph.nodes())} nodos")
    
    def detect_circular_imports(self) -> Dict[str, List[List[str]]]:
        """Detecta importaciones circulares en el grafo de importaciones.
        
        Returns:
            Diccionario con módulos que tienen importaciones circulares y sus ciclos
        """
        circular_imports = {}
        
        try:
            # Buscar ciclos en el grafo
            cycles = list(nx.simple_cycles(self.import_graph))
            
            # Agrupar ciclos por módulos
            for module in self.import_graph.nodes():
                module_cycles = [cycle for cycle in cycles if module in cycle]
                if module_cycles:
                    circular_imports[module] = module_cycles
            
            logger.info(f"Detectados {len(circular_imports)} módulos con importaciones circulares")
            return circular_imports
            
        except Exception as e:
            logger.error(f"Error detectando importaciones circulares: {str(e)}")
            return {}
    
    def detect_problematic_patterns(self) -> Dict[str, List[Tuple[int, str, str]]]:
        """Detecta patrones de importación problemáticos.
        
        Returns:
            Diccionario con archivos que contienen patrones problemáticos
        """
        problematic_files = {}
        
        for file_path in self._get_python_files():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                problematic_lines = []
                for i, line in enumerate(content.splitlines(), 1):
                    for pattern in self.problematic_patterns:
                        match = re.search(pattern, line)
                        if match:
                            # Guarda línea, número y patrón detectado
                            problematic_lines.append((i, line, match.group(0)))
                
                if problematic_lines:
                    relative_path = str(file_path.relative_to(self.base_path))
                    problematic_files[relative_path] = problematic_lines
                    
            except Exception as e:
                logger.error(f"Error analizando {file_path}: {str(e)}")
        
        logger.info(f"Detectados {len(problematic_files)} archivos con patrones de importación problemáticos")
        return problematic_files
    
    def suggest_fixes(self, problematic_files: Dict[str, List[Tuple[int, str, str]]]) -> Dict[str, List[Tuple[int, str, str]]]:
        """Sugiere correcciones para los patrones de importación problemáticos.
        
        Args:
            problematic_files: Diccionario con archivos y sus problemas detectados
            
        Returns:
            Diccionario con archivos y sugerencias de corrección
        """
        suggestions = {}
        
        for file_path, issues in problematic_files.items():
            file_suggestions = []
            
            for line_num, line, pattern in issues:
                if "from app.import_config import get_" in pattern:
                    # Extraer nombre del getter
                    getter_name = re.search(r'get_(\w+)', pattern)
                    if getter_name:
                        module_name = getter_name.group(1)
                        
                        # Crear sugerencia basada en el tipo de getter
                        if "handler" in module_name:
                            suggested = f"from app.com.chatbot.handlers.{module_name} import {module_name.capitalize()}Handler"
                        elif "processor" in module_name:
                            suggested = f"from app.com.chatbot.processors.{module_name} import {module_name.capitalize()}Processor"
                        else:
                            suggested = f"# Importar directamente: from app.<module>.{module_name} import {module_name.capitalize()}"
                        
                        file_suggestions.append((line_num, line, suggested))
                
                elif re.search(r'from app\.(com|ml|pagos|publish|sexsi|utilidades)\.import_config import', pattern):
                    # Sugerir migración a importaciones directas
                    module = re.search(r'from app\.(\w+)\.import_config', pattern).group(1)
                    imported = re.search(r'import (.+)', line)
                    if imported:
                        items = [item.strip() for item in imported.group(1).split(',')]
                        for item in items:
                            if item.startswith('get_'):
                                target = item[4:]  # Quitar 'get_'
                                suggested = f"from app.{module}.{target} import {target.capitalize()}"
                                file_suggestions.append((line_num, line, suggested))
                
                elif "from ." in pattern:
                    # Convertir importaciones relativas a absolutas
                    file_module = os.path.dirname(file_path).replace('/', '.')
                    relative_import = re.search(r'from \.([^ ]+) import', pattern)
                    if relative_import:
                        rel_module = relative_import.group(1)
                        if file_module.startswith('app.'):
                            suggested = line.replace(f"from .{rel_module}", f"from {file_module}.{rel_module}")
                            file_suggestions.append((line_num, line, suggested))
            
            if file_suggestions:
                suggestions[file_path] = file_suggestions
        
        return suggestions
    
    def fix_file(self, file_path: str, suggestions: List[Tuple[int, str, str]]) -> bool:
        """Aplica las correcciones sugeridas a un archivo.
        
        Args:
            file_path: Ruta al archivo a corregir
            suggestions: Lista de sugerencias (línea, original, corrección)
            
        Returns:
            True si se aplicó alguna corrección, False en caso contrario
        """
        try:
            absolute_path = self.base_path / file_path
            with open(absolute_path, 'r', encoding='utf-8') as f:
                content = f.readlines()
            
            changes_made = False
            for line_num, original, suggested in suggestions:
                if not suggested.startswith('#'):  # No aplicar comentarios
                    # Líneas son 0-indexed en la lista, pero 1-indexed en las sugerencias
                    content[line_num - 1] = suggested + '\n'
                    changes_made = True
            
            if changes_made:
                # Crear copia de seguridad
                backup_path = str(absolute_path) + '.bak'
                with open(backup_path, 'w', encoding='utf-8') as f:
                    with open(absolute_path, 'r', encoding='utf-8') as original:
                        f.write(original.read())
                
                # Escribir versión corregida
                with open(absolute_path, 'w', encoding='utf-8') as f:
                    f.writelines(content)
                
                logger.info(f"Corregido {file_path}, backup guardado en {backup_path}")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error corrigiendo {file_path}: {str(e)}")
            return False
    
    def generate_report(self) -> Dict[str, Any]:
        """Genera un informe completo de análisis.
        
        Returns:
            Informe detallado del análisis
        """
        circular_imports = self.detect_circular_imports()
        problematic_patterns = self.detect_problematic_patterns()
        suggestions = self.suggest_fixes(problematic_patterns)
        
        # Calcular estadísticas
        total_files = len(list(self._get_python_files()))
        files_with_issues = len(problematic_patterns)
        percentage = (files_with_issues / total_files) * 100 if total_files > 0 else 0
        
        return {
            "total_files": total_files,
            "files_with_issues": files_with_issues,
            "percentage": percentage,
            "circular_imports": circular_imports,
            "problematic_patterns": problematic_patterns,
            "suggestions": suggestions
        }
    
    def _get_python_files(self) -> List[Path]:
        """Obtiene todos los archivos Python del proyecto, excluyendo directorios ignorados.
        
        Returns:
            Lista de rutas a archivos Python
        """
        python_files = []
        for root, dirs, files in os.walk(self.base_path):
            # Excluir directorios ignorados
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
            
            for file in files:
                if file.endswith('.py') and file not in self.ignore_files:
                    file_path = Path(os.path.join(root, file))
                    python_files.append(file_path)
        
        return python_files
    
    def _analyze_file(self, file_path: Path) -> None:
        """Analiza un archivo para extraer sus importaciones.
        
        Args:
            file_path: Ruta al archivo a analizar
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Convertir a módulo
            relative_path = file_path.relative_to(self.base_path)
            module_path = str(relative_path).replace('/', '.').replace('.py', '')
            
            # Ignorar archivos __init__.py
            if module_path.endswith('__init__'):
                return
            
            self.import_graph.add_node(module_path)
            
            # Extraer importaciones
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imported_module = name.name
                        self.import_graph.add_edge(module_path, imported_module)
                        
                elif isinstance(node, ast.ImportFrom):
                    if node.module is not None:
                        if node.level > 0:  # Importación relativa
                            # Convertir a ruta absoluta
                            parts = module_path.split('.')
                            if node.level <= len(parts):
                                parent = '.'.join(parts[:-node.level])
                                if node.module:
                                    imported_module = f"{parent}.{node.module}"
                                else:
                                    imported_module = parent
                                self.import_graph.add_edge(module_path, imported_module)
                        else:
                            imported_module = node.module
                            self.import_graph.add_edge(module_path, imported_module)
                            
        except Exception as e:
            logger.error(f"Error analizando importaciones en {file_path}: {str(e)}")


def main():
    """Función principal para ejecutar el analizador desde línea de comandos."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analizador de importaciones para detectar y corregir problemas.')
    parser.add_argument('--path', type=str, default=None, help='Ruta base del proyecto a analizar')
    parser.add_argument('--fix', action='store_true', help='Aplicar correcciones automáticas')
    parser.add_argument('--report', action='store_true', help='Generar informe detallado')
    
    args = parser.parse_args()
    
    analyzer = ImportAnalyzer(args.path)
    analyzer.scan_project()
    
    if args.report:
        report = analyzer.generate_report()
        print("\n===== INFORME DE ANÁLISIS DE IMPORTACIONES =====")
        print(f"Total de archivos analizados: {report['total_files']}")
        print(f"Archivos con problemas: {report['files_with_issues']} ({report['percentage']:.2f}%)")
        
        print("\n--- PATRONES PROBLEMÁTICOS ---")
        for file, issues in report['problematic_patterns'].items():
            print(f"\n{file}:")
            for line_num, line, pattern in issues:
                print(f"  Línea {line_num}: {line.strip()}")
        
        print("\n--- IMPORTACIONES CIRCULARES ---")
        for module, cycles in report['circular_imports'].items():
            print(f"\n{module} participa en {len(cycles)} ciclos:")
            for cycle in cycles[:3]:  # Mostrar sólo los primeros 3 ciclos
                print(f"  {' -> '.join(cycle)} -> {cycle[0]}")
            if len(cycles) > 3:
                print(f"  ... y {len(cycles) - 3} más")
        
        print("\n--- SUGERENCIAS DE CORRECCIÓN ---")
        for file, suggestions in report['suggestions'].items():
            print(f"\n{file}:")
            for line_num, original, suggested in suggestions:
                print(f"  Línea {line_num}:")
                print(f"    Original: {original.strip()}")
                print(f"    Sugerida: {suggested}")
    
    if args.fix:
        problematic_patterns = analyzer.detect_problematic_patterns()
        suggestions = analyzer.suggest_fixes(problematic_patterns)
        
        fixed_files = 0
        for file_path, file_suggestions in suggestions.items():
            if analyzer.fix_file(file_path, file_suggestions):
                fixed_files += 1
        
        print(f"\nSe corrigieron automáticamente {fixed_files} archivos.")
        print("Se crearon copias de seguridad con extensión .bak para cada archivo modificado.")
    
    if not args.report and not args.fix:
        # Modo rápido - solo mostrar estadísticas básicas
        problematic_patterns = analyzer.detect_problematic_patterns()
        circular_imports = analyzer.detect_circular_imports()
        
        print("\n===== RESUMEN DE PROBLEMAS DE IMPORTACIÓN =====")
        print(f"Archivos con patrones problemáticos: {len(problematic_patterns)}")
        print(f"Módulos con importaciones circulares: {len(circular_imports)}")
        print("\nEjecute con --report para ver detalles o --fix para aplicar correcciones automáticas.")


if __name__ == "__main__":
    main()
