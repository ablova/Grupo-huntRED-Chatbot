"""
AURA - Multi-Platform Connector (FASE 2)
Conectores avanzados para múltiples plataformas profesionales
"""

import logging
import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import asyncio
import aiohttp
from urllib.parse import urlencode
import hashlib
import hmac

logger = logging.getLogger(__name__)

# CONFIGURACIÓN: DESHABILITADO POR DEFECTO
ENABLED = False  # Cambiar a True para habilitar


@dataclass
class PlatformData:
    """Datos de una plataforma específica"""
    platform: str
    user_id: str
    profile_data: Dict[str, Any]
    connections: List[Dict[str, Any]]
    posts: List[Dict[str, Any]]
    activities: List[Dict[str, Any]]
    last_sync: datetime
    sync_status: str  # 'success', 'error', 'pending'
    error_message: Optional[str] = None


@dataclass
class SyncResult:
    """Resultado de sincronización"""
    platform: str
    success: bool
    data_count: int
    new_connections: int
    new_posts: int
    new_activities: int
    sync_time: datetime
    duration_seconds: float
    error_message: Optional[str] = None


class BaseConnector(ABC):
    """Clase base para conectores de plataformas"""
    
    def __init__(self, platform_name: str, api_key: str = None, api_secret: str = None):
        self.platform_name = platform_name
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = ""
        self.rate_limit_delay = 1.0  # segundos entre requests
        self.last_request_time = 0
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Autentica con la plataforma"""
        pass
    
    @abstractmethod
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Obtiene perfil del usuario"""
        pass
    
    @abstractmethod
    async def get_connections(self, user_id: str) -> List[Dict[str, Any]]:
        """Obtiene conexiones del usuario"""
        pass
    
    @abstractmethod
    async def get_posts(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtiene posts del usuario"""
        pass
    
    @abstractmethod
    async def get_activities(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtiene actividades del usuario"""
        pass
    
    def _rate_limit(self):
        """Implementa rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    def _make_request(self, url: str, headers: Dict[str, str] = None, 
                     params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Realiza request HTTP con rate limiting"""
        self._rate_limit()
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to {url}: {e}")
            return {}


class LinkedInConnector(BaseConnector):
    """Conector para LinkedIn"""
    
    def __init__(self, api_key: str = None, api_secret: str = None):
        super().__init__("linkedin", api_key, api_secret)
        self.base_url = "https://api.linkedin.com/v2"
        self.access_token = None
    
    async def authenticate(self) -> bool:
        """Autentica con LinkedIn API"""
        if not self.enabled:
            return True
        
        try:
            # En implementación real, usar OAuth 2.0
            # Por ahora, simulación
            self.access_token = "mock_access_token"
            return True
        except Exception as e:
            logger.error(f"LinkedIn authentication error: {e}")
            return False
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Obtiene perfil de LinkedIn"""
        if not self.enabled:
            return self._get_mock_profile(user_id)
        
        try:
            url = f"{self.base_url}/me"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            data = self._make_request(url, headers=headers)
            
            return {
                "id": data.get("id", user_id),
                "name": data.get("localizedFirstName", "") + " " + data.get("localizedLastName", ""),
                "headline": data.get("headline", ""),
                "summary": data.get("summary", ""),
                "location": data.get("location", {}).get("name", ""),
                "industry": data.get("industry", ""),
                "profile_picture": data.get("profilePicture", {}).get("displayImage", ""),
                "public_profile_url": data.get("publicProfileUrl", ""),
                "connections_count": data.get("numConnections", 0),
                "skills": data.get("skills", []),
                "experience": data.get("experience", []),
                "education": data.get("education", [])
            }
        except Exception as e:
            logger.error(f"Error getting LinkedIn profile: {e}")
            return self._get_mock_profile(user_id)
    
    async def get_connections(self, user_id: str) -> List[Dict[str, Any]]:
        """Obtiene conexiones de LinkedIn"""
        if not self.enabled:
            return self._get_mock_connections(user_id)
        
        try:
            url = f"{self.base_url}/connections"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            data = self._make_request(url, headers=headers)
            connections = data.get("elements", [])
            
            return [
                {
                    "id": conn.get("id"),
                    "name": conn.get("localizedFirstName", "") + " " + conn.get("localizedLastName", ""),
                    "headline": conn.get("headline", ""),
                    "profile_url": conn.get("publicProfileUrl", ""),
                    "connection_date": conn.get("connectionDate", ""),
                    "mutual_connections": conn.get("mutualConnections", 0)
                }
                for conn in connections
            ]
        except Exception as e:
            logger.error(f"Error getting LinkedIn connections: {e}")
            return self._get_mock_connections(user_id)
    
    async def get_posts(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtiene posts de LinkedIn"""
        if not self.enabled:
            return self._get_mock_posts(user_id, limit)
        
        try:
            url = f"{self.base_url}/ugcPosts"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            params = {"authors": f"urn:li:person:{user_id}", "count": limit}
            
            data = self._make_request(url, headers=headers, params=params)
            posts = data.get("elements", [])
            
            return [
                {
                    "id": post.get("id"),
                    "content": post.get("specificContent", {}).get("com.linkedin.ugc.ShareContent", {}).get("text", ""),
                    "created_time": post.get("created", {}).get("time", ""),
                    "likes_count": post.get("socialDetail", {}).get("totalSocialActivityCounts", {}).get("numLikes", 0),
                    "comments_count": post.get("socialDetail", {}).get("totalSocialActivityCounts", {}).get("numComments", 0),
                    "shares_count": post.get("socialDetail", {}).get("totalSocialActivityCounts", {}).get("numShares", 0)
                }
                for post in posts
            ]
        except Exception as e:
            logger.error(f"Error getting LinkedIn posts: {e}")
            return self._get_mock_posts(user_id, limit)
    
    async def get_activities(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtiene actividades de LinkedIn"""
        if not self.enabled:
            return self._get_mock_activities(user_id, limit)
        
        try:
            # LinkedIn no tiene API directa para actividades
            # Usar posts como proxy de actividades
            posts = await self.get_posts(user_id, limit)
            
            return [
                {
                    "id": f"activity_{post['id']}",
                    "type": "post",
                    "content": post["content"],
                    "timestamp": post["created_time"],
                    "engagement": post["likes_count"] + post["comments_count"] + post["shares_count"]
                }
                for post in posts
            ]
        except Exception as e:
            logger.error(f"Error getting LinkedIn activities: {e}")
            return self._get_mock_activities(user_id, limit)
    
    def _get_mock_profile(self, user_id: str) -> Dict[str, Any]:
        """Perfil simulado"""
        return {
            "id": user_id,
            "name": "John Doe",
            "headline": "Senior Software Engineer at Tech Corp",
            "summary": "Experienced software engineer with expertise in Python and ML",
            "location": "San Francisco, CA",
            "industry": "Technology",
            "profile_picture": "https://example.com/profile.jpg",
            "public_profile_url": f"https://linkedin.com/in/{user_id}",
            "connections_count": 250,
            "skills": ["Python", "Machine Learning", "Data Science"],
            "experience": [
                {
                    "title": "Senior Software Engineer",
                    "company": "Tech Corp",
                    "duration": "2020-Present"
                }
            ],
            "education": [
                {
                    "degree": "Master of Science",
                    "school": "Stanford University",
                    "year": "2020"
                }
            ]
        }
    
    def _get_mock_connections(self, user_id: str) -> List[Dict[str, Any]]:
        """Conexiones simuladas"""
        return [
            {
                "id": "conn_1",
                "name": "Jane Smith",
                "headline": "Product Manager at Startup",
                "profile_url": "https://linkedin.com/in/jane-smith",
                "connection_date": "2023-01-15",
                "mutual_connections": 15
            },
            {
                "id": "conn_2",
                "name": "Bob Johnson",
                "headline": "Data Scientist at Big Tech",
                "profile_url": "https://linkedin.com/in/bob-johnson",
                "connection_date": "2023-03-20",
                "mutual_connections": 8
            }
        ]
    
    def _get_mock_posts(self, user_id: str, limit: int) -> List[Dict[str, Any]]:
        """Posts simulados"""
        return [
            {
                "id": "post_1",
                "content": "Excited to share my latest project on machine learning!",
                "created_time": "2024-01-15T10:30:00Z",
                "likes_count": 45,
                "comments_count": 12,
                "shares_count": 5
            },
            {
                "id": "post_2",
                "content": "Great insights from the AI conference today.",
                "created_time": "2024-01-10T14:20:00Z",
                "likes_count": 32,
                "comments_count": 8,
                "shares_count": 3
            }
        ]
    
    def _get_mock_activities(self, user_id: str, limit: int) -> List[Dict[str, Any]]:
        """Actividades simuladas"""
        return [
            {
                "id": "activity_1",
                "type": "post",
                "content": "Excited to share my latest project on machine learning!",
                "timestamp": "2024-01-15T10:30:00Z",
                "engagement": 62
            },
            {
                "id": "activity_2",
                "type": "connection",
                "content": "Connected with Jane Smith",
                "timestamp": "2024-01-14T16:45:00Z",
                "engagement": 1
            }
        ]


class GitHubConnector(BaseConnector):
    """Conector para GitHub"""
    
    def __init__(self, api_key: str = None):
        super().__init__("github", api_key)
        self.base_url = "https://api.github.com"
        self.headers = {"Authorization": f"token {api_key}"} if api_key else {}
    
    async def authenticate(self) -> bool:
        """Autentica con GitHub API"""
        if not self.enabled:
            return True
        
        try:
            url = f"{self.base_url}/user"
            response = requests.get(url, headers=self.headers, timeout=30)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"GitHub authentication error: {e}")
            return False
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Obtiene perfil de GitHub"""
        if not self.enabled:
            return self._get_mock_profile(user_id)
        
        try:
            url = f"{self.base_url}/users/{user_id}"
            data = self._make_request(url, headers=self.headers)
            
            return {
                "id": data.get("id"),
                "username": data.get("login"),
                "name": data.get("name", ""),
                "bio": data.get("bio", ""),
                "location": data.get("location", ""),
                "company": data.get("company", ""),
                "blog": data.get("blog", ""),
                "public_repos": data.get("public_repos", 0),
                "public_gists": data.get("public_gists", 0),
                "followers": data.get("followers", 0),
                "following": data.get("following", 0),
                "created_at": data.get("created_at", ""),
                "updated_at": data.get("updated_at", ""),
                "avatar_url": data.get("avatar_url", "")
            }
        except Exception as e:
            logger.error(f"Error getting GitHub profile: {e}")
            return self._get_mock_profile(user_id)
    
    async def get_connections(self, user_id: str) -> List[Dict[str, Any]]:
        """Obtiene followers/following de GitHub"""
        if not self.enabled:
            return self._get_mock_connections(user_id)
        
        try:
            # Obtener followers
            followers_url = f"{self.base_url}/users/{user_id}/followers"
            followers_data = self._make_request(followers_url, headers=self.headers)
            
            connections = []
            for follower in followers_data[:50]:  # Limitar a 50
                connections.append({
                    "id": follower.get("id"),
                    "username": follower.get("login"),
                    "name": follower.get("name", ""),
                    "avatar_url": follower.get("avatar_url", ""),
                    "profile_url": follower.get("html_url", ""),
                    "type": "follower"
                })
            
            return connections
        except Exception as e:
            logger.error(f"Error getting GitHub connections: {e}")
            return self._get_mock_connections(user_id)
    
    async def get_posts(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtiene repositorios como 'posts'"""
        if not self.enabled:
            return self._get_mock_posts(user_id, limit)
        
        try:
            url = f"{self.base_url}/users/{user_id}/repos"
            params = {"sort": "updated", "per_page": limit}
            data = self._make_request(url, headers=self.headers, params=params)
            
            return [
                {
                    "id": repo.get("id"),
                    "name": repo.get("name"),
                    "description": repo.get("description", ""),
                    "language": repo.get("language", ""),
                    "stars": repo.get("stargazers_count", 0),
                    "forks": repo.get("forks_count", 0),
                    "created_at": repo.get("created_at", ""),
                    "updated_at": repo.get("updated_at", ""),
                    "url": repo.get("html_url", "")
                }
                for repo in data
            ]
        except Exception as e:
            logger.error(f"Error getting GitHub repos: {e}")
            return self._get_mock_posts(user_id, limit)
    
    async def get_activities(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtiene actividades de GitHub"""
        if not self.enabled:
            return self._get_mock_activities(user_id, limit)
        
        try:
            # Obtener eventos públicos
            url = f"{self.base_url}/users/{user_id}/events"
            params = {"per_page": limit}
            data = self._make_request(url, headers=self.headers, params=params)
            
            return [
                {
                    "id": event.get("id"),
                    "type": event.get("type", ""),
                    "repo": event.get("repo", {}).get("name", ""),
                    "created_at": event.get("created_at", ""),
                    "payload": event.get("payload", {})
                }
                for event in data
            ]
        except Exception as e:
            logger.error(f"Error getting GitHub activities: {e}")
            return self._get_mock_activities(user_id, limit)
    
    def _get_mock_profile(self, user_id: str) -> Dict[str, Any]:
        """Perfil simulado"""
        return {
            "id": 12345,
            "username": user_id,
            "name": "John Doe",
            "bio": "Software engineer passionate about open source",
            "location": "San Francisco, CA",
            "company": "Tech Corp",
            "blog": "https://johndoe.dev",
            "public_repos": 25,
            "public_gists": 5,
            "followers": 150,
            "following": 80,
            "created_at": "2020-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z",
            "avatar_url": "https://github.com/avatars/johndoe.jpg"
        }
    
    def _get_mock_connections(self, user_id: str) -> List[Dict[str, Any]]:
        """Conexiones simuladas"""
        return [
            {
                "id": 67890,
                "username": "jane-smith",
                "name": "Jane Smith",
                "avatar_url": "https://github.com/avatars/jane-smith.jpg",
                "profile_url": "https://github.com/jane-smith",
                "type": "follower"
            }
        ]
    
    def _get_mock_posts(self, user_id: str, limit: int) -> List[Dict[str, Any]]:
        """Repositorios simulados"""
        return [
            {
                "id": 123456,
                "name": "ml-project",
                "description": "Machine learning project for sentiment analysis",
                "language": "Python",
                "stars": 45,
                "forks": 12,
                "created_at": "2023-06-15T10:30:00Z",
                "updated_at": "2024-01-10T14:20:00Z",
                "url": "https://github.com/johndoe/ml-project"
            }
        ]
    
    def _get_mock_activities(self, user_id: str, limit: int) -> List[Dict[str, Any]]:
        """Actividades simuladas"""
        return [
            {
                "id": 789012,
                "type": "PushEvent",
                "repo": "johndoe/ml-project",
                "created_at": "2024-01-15T10:30:00Z",
                "payload": {"commits": 3}
            }
        ]


class MultiPlatformConnector:
    """
    Conector principal para múltiples plataformas
    """
    
    def __init__(self):
        self.enabled = ENABLED
        if not self.enabled:
            logger.info("MultiPlatformConnector: DESHABILITADO")
            return
        
        self.connectors = {
            "linkedin": LinkedInConnector(),
            "github": GitHubConnector(),
            # Agregar más conectores aquí
        }
        
        self.sync_history = {}
        logger.info("MultiPlatformConnector: Inicializado")
    
    async def sync_user_data(self, user_id: str, platforms: List[str]) -> List[SyncResult]:
        """
        Sincroniza datos de usuario desde múltiples plataformas
        """
        if not self.enabled:
            return self._get_mock_sync_results(user_id, platforms)
        
        results = []
        
        for platform in platforms:
            if platform not in self.connectors:
                logger.warning(f"Connector not available for platform: {platform}")
                continue
            
            start_time = time.time()
            connector = self.connectors[platform]
            
            try:
                # Autenticar
                if not await connector.authenticate():
                    results.append(SyncResult(
                        platform=platform,
                        success=False,
                        data_count=0,
                        new_connections=0,
                        new_posts=0,
                        new_activities=0,
                        sync_time=datetime.now(),
                        duration_seconds=time.time() - start_time,
                        error_message="Authentication failed"
                    ))
                    continue
                
                # Obtener datos
                profile = await connector.get_user_profile(user_id)
                connections = await connector.get_connections(user_id)
                posts = await connector.get_posts(user_id)
                activities = await connector.get_activities(user_id)
                
                # Guardar datos
                platform_data = PlatformData(
                    platform=platform,
                    user_id=user_id,
                    profile_data=profile,
                    connections=connections,
                    posts=posts,
                    activities=activities,
                    last_sync=datetime.now(),
                    sync_status="success"
                )
                
                # Actualizar historial
                self.sync_history[f"{user_id}_{platform}"] = platform_data
                
                results.append(SyncResult(
                    platform=platform,
                    success=True,
                    data_count=len(connections) + len(posts) + len(activities),
                    new_connections=len(connections),
                    new_posts=len(posts),
                    new_activities=len(activities),
                    sync_time=datetime.now(),
                    duration_seconds=time.time() - start_time
                ))
                
            except Exception as e:
                logger.error(f"Error syncing {platform} for user {user_id}: {e}")
                results.append(SyncResult(
                    platform=platform,
                    success=False,
                    data_count=0,
                    new_connections=0,
                    new_posts=0,
                    new_activities=0,
                    sync_time=datetime.now(),
                    duration_seconds=time.time() - start_time,
                    error_message=str(e)
                ))
        
        return results
    
    async def get_consolidated_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Obtiene perfil consolidado de todas las plataformas
        """
        if not self.enabled:
            return self._get_mock_consolidated_profile(user_id)
        
        try:
            consolidated = {
                "user_id": user_id,
                "platforms": {},
                "consolidated_data": {
                    "name": "",
                    "headline": "",
                    "location": "",
                    "skills": [],
                    "experience": [],
                    "education": [],
                    "total_connections": 0,
                    "total_posts": 0,
                    "total_activities": 0
                },
                "last_sync": datetime.now().isoformat()
            }
            
            # Consolidar datos de todas las plataformas
            for platform, platform_data in self.sync_history.items():
                if platform.startswith(f"{user_id}_"):
                    platform_name = platform.split("_", 1)[1]
                    consolidated["platforms"][platform_name] = platform_data.profile_data
                    
                    # Consolidar datos principales
                    if not consolidated["consolidated_data"]["name"] and platform_data.profile_data.get("name"):
                        consolidated["consolidated_data"]["name"] = platform_data.profile_data["name"]
                    
                    if not consolidated["consolidated_data"]["headline"] and platform_data.profile_data.get("headline"):
                        consolidated["consolidated_data"]["headline"] = platform_data.profile_data["headline"]
                    
                    if not consolidated["consolidated_data"]["location"] and platform_data.profile_data.get("location"):
                        consolidated["consolidated_data"]["location"] = platform_data.profile_data["location"]
                    
                    # Consolidar habilidades
                    skills = platform_data.profile_data.get("skills", [])
                    consolidated["consolidated_data"]["skills"].extend(skills)
                    
                    # Consolidar conexiones
                    consolidated["consolidated_data"]["total_connections"] += len(platform_data.connections)
                    consolidated["consolidated_data"]["total_posts"] += len(platform_data.posts)
                    consolidated["consolidated_data"]["total_activities"] += len(platform_data.activities)
            
            # Remover duplicados de habilidades
            consolidated["consolidated_data"]["skills"] = list(set(consolidated["consolidated_data"]["skills"]))
            
            return consolidated
            
        except Exception as e:
            logger.error(f"Error getting consolidated profile: {e}")
            return self._get_mock_consolidated_profile(user_id)
    
    def get_sync_status(self, user_id: str) -> Dict[str, Any]:
        """
        Obtiene estado de sincronización del usuario
        """
        if not self.enabled:
            return self._get_mock_sync_status(user_id)
        
        try:
            status = {
                "user_id": user_id,
                "platforms": {},
                "last_sync": None,
                "overall_status": "unknown"
            }
            
            for platform, platform_data in self.sync_history.items():
                if platform.startswith(f"{user_id}_"):
                    platform_name = platform.split("_", 1)[1]
                    status["platforms"][platform_name] = {
                        "sync_status": platform_data.sync_status,
                        "last_sync": platform_data.last_sync.isoformat(),
                        "data_count": len(platform_data.connections) + len(platform_data.posts) + len(platform_data.activities),
                        "error_message": platform_data.error_message
                    }
                    
                    if not status["last_sync"] or platform_data.last_sync > datetime.fromisoformat(status["last_sync"]):
                        status["last_sync"] = platform_data.last_sync.isoformat()
            
            # Determinar estado general
            if status["platforms"]:
                success_count = sum(1 for p in status["platforms"].values() if p["sync_status"] == "success")
                if success_count == len(status["platforms"]):
                    status["overall_status"] = "success"
                elif success_count > 0:
                    status["overall_status"] = "partial"
                else:
                    status["overall_status"] = "error"
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting sync status: {e}")
            return self._get_mock_sync_status(user_id)
    
    def _get_mock_sync_results(self, user_id: str, platforms: List[str]) -> List[SyncResult]:
        """Resultados de sincronización simulados"""
        results = []
        for platform in platforms:
            results.append(SyncResult(
                platform=platform,
                success=True,
                data_count=100,
                new_connections=25,
                new_posts=10,
                new_activities=15,
                sync_time=datetime.now(),
                duration_seconds=2.5
            ))
        return results
    
    def _get_mock_consolidated_profile(self, user_id: str) -> Dict[str, Any]:
        """Perfil consolidado simulado"""
        return {
            "user_id": user_id,
            "platforms": {
                "linkedin": {"name": "John Doe", "headline": "Software Engineer"},
                "github": {"username": "johndoe", "bio": "Open source enthusiast"}
            },
            "consolidated_data": {
                "name": "John Doe",
                "headline": "Software Engineer",
                "location": "San Francisco, CA",
                "skills": ["Python", "Machine Learning", "Data Science"],
                "experience": [],
                "education": [],
                "total_connections": 250,
                "total_posts": 50,
                "total_activities": 100
            },
            "last_sync": datetime.now().isoformat()
        }
    
    def _get_mock_sync_status(self, user_id: str) -> Dict[str, Any]:
        """Estado de sincronización simulado"""
        return {
            "user_id": user_id,
            "platforms": {
                "linkedin": {
                    "sync_status": "success",
                    "last_sync": datetime.now().isoformat(),
                    "data_count": 100,
                    "error_message": None
                },
                "github": {
                    "sync_status": "success",
                    "last_sync": datetime.now().isoformat(),
                    "data_count": 50,
                    "error_message": None
                }
            },
            "last_sync": datetime.now().isoformat(),
            "overall_status": "success"
        }


# Instancia global del conector multiplataforma
multi_platform_connector = MultiPlatformConnector() 