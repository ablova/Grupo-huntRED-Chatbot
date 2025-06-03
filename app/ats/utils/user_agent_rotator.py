import asyncio
import random
import time
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class UserAgentRotator:
    """Sistema avanzado de rotación de User-Agents para evitar detección."""
    
    def __init__(self):
        self.user_agents = {
            'desktop': {
                'chrome': [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ],
                'firefox': [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
                    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0"
                ],
                'safari': [
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"
                ],
                'edge': [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
                ]
            },
            'mobile': {
                'android': [
                    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
                    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
                ],
                'ios': [
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
                    "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
                ]
            }
        }
        self.last_used = {}
        self.usage_count = {}
        self.lock = asyncio.Lock()
        
    async def get_user_agent(self, device_type: str = 'desktop', browser: str = None) -> str:
        """
        Obtiene un User-Agent aleatorio con estrategia de rotación inteligente.
        
        Args:
            device_type: 'desktop' o 'mobile'
            browser: Navegador específico (opcional)
            
        Returns:
            str: User-Agent seleccionado
        """
        async with self.lock:
            # Seleccionar grupo de User-Agents
            if device_type not in self.user_agents:
                device_type = 'desktop'
                
            if browser:
                available_agents = self.user_agents[device_type].get(browser, [])
            else:
                # Combinar todos los User-Agents del tipo de dispositivo
                available_agents = []
                for browser_agents in self.user_agents[device_type].values():
                    available_agents.extend(browser_agents)
            
            if not available_agents:
                raise ValueError(f"No hay User-Agents disponibles para {device_type}/{browser}")
            
            # Implementar estrategia de rotación
            now = time.time()
            valid_agents = []
            
            for agent in available_agents:
                last_used = self.last_used.get(agent, 0)
                usage_count = self.usage_count.get(agent, 0)
                
                # Si el agente no se ha usado en los últimos 5 minutos o tiene bajo uso
                if now - last_used > 300 or usage_count < 3:
                    valid_agents.append(agent)
            
            # Si no hay agentes válidos, resetear contadores
            if not valid_agents:
                self.last_used.clear()
                self.usage_count.clear()
                valid_agents = available_agents
            
            # Seleccionar agente aleatorio
            selected_agent = random.choice(valid_agents)
            
            # Actualizar contadores
            self.last_used[selected_agent] = now
            self.usage_count[selected_agent] = self.usage_count.get(selected_agent, 0) + 1
            
            return selected_agent
    
    async def get_headers(self, device_type: str = 'desktop', browser: str = None) -> dict:
        """
        Obtiene headers completos con User-Agent y otros headers comunes.
        
        Args:
            device_type: 'desktop' o 'mobile'
            browser: Navegador específico (opcional)
            
        Returns:
            dict: Headers completos
        """
        user_agent = await self.get_user_agent(device_type, browser)
        
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        
        # Agregar headers específicos según el navegador
        if browser == 'chrome':
            headers['Sec-Ch-Ua'] = '"Not_A Brand";v="8", "Chromium";v="120"'
            headers['Sec-Ch-Ua-Mobile'] = '?0'
            headers['Sec-Ch-Ua-Platform'] = '"Windows"'
        elif browser == 'firefox':
            headers['DNT'] = '1'
        elif browser == 'safari':
            headers['Sec-Ch-Ua-Platform'] = '"macOS"'
        
        return headers 