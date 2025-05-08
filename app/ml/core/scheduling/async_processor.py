import asyncio
from typing import Callable, Tuple, List, Any
import concurrent.futures
from functools import partial

class AsyncProcessor:
    """
    Procesador asíncrono para el sistema ATS AI.
    
    Esta clase permite procesar múltiples tareas de manera asíncrona,
    mejorando el rendimiento del sistema.
    """
    
    def __init__(self, max_workers: int = None):
        """
        Inicializa el procesador asíncrono.
        
        Args:
            max_workers: Número máximo de workers (opcional)
        """
        self.max_workers = max_workers
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    async def process(self, tasks: List[Tuple[Callable, ...]]) -> List[Any]:
        """
        Procesa múltiples tareas de manera asíncrona.
        
        Args:
            tasks: Lista de tuplas con funciones y argumentos
            
        Returns:
            List[Any]: Resultados de las tareas
        """
        loop = asyncio.get_event_loop()
        futures = []
        
        for task in tasks:
            func = task[0]
            args = task[1:]
            
            # Crear función parcial con argumentos
            partial_func = partial(func, *args)
            
            # Crear tarea asíncrona
            future = loop.run_in_executor(self.executor, partial_func)
            futures.append(future)
        
        # Esperar resultados
        results = await asyncio.gather(*futures)
        return results

    def process_sync(self, tasks: List[Tuple[Callable, ...]]) -> List[Any]:
        """
        Procesa múltiples tareas de manera asíncrona desde un contexto sincrónico.
        
        Args:
            tasks: Lista de tuplas con funciones y argumentos
            
        Returns:
            List[Any]: Resultados de las tareas
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(self.process(tasks))
            return results
        finally:
            loop.close()

    def shutdown(self) -> None:
        """
        Cierra el procesador y libera recursos.
        """
        self.executor.shutdown()
