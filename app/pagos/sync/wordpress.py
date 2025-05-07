import requests
from django.conf import settings
from app.pagos.models import Oportunidad, Empleador

class WordPressSync:
    def __init__(self):
        self.base_url = settings.WORDPRESS_API_URL
        self.auth = (settings.WORDPRESS_USERNAME, settings.WORDPRESS_PASSWORD)

    def sincronizar_oportunidad(self, oportunidad: Oportunidad):
        """Sincroniza una oportunidad con WordPress"""
        data = {
            'title': oportunidad.titulo,
            'content': oportunidad.descripcion,
            'status': 'publish',
            'meta': {
                'tipo_contrato': oportunidad.tipo_contrato,
                'salario_minimo': str(oportunidad.salario_minimo),
                'salario_maximo': str(oportunidad.salario_maximo),
                'pais': oportunidad.pais,
                'ciudad': oportunidad.ciudad,
                'modalidad': oportunidad.modalidad,
                'empleador_id': oportunidad.empleador.id
            }
        }

        response = requests.post(
            f"{self.base_url}/wp-json/wp/v2/posts",
            json=data,
            auth=self.auth
        )

        if response.status_code == 201:
            return True, response.json()
        return False, response.json()

    def sincronizar_empleador(self, empleador: Empleador):
        """Sincroniza un empleador con WordPress"""
        data = {
            'title': empleador.razon_social,
            'content': f"Razón social: {empleador.razon_social}\n"
                      f"RFC: {empleador.rfc}\n"
                      f"Dirección: {empleador.direccion_fiscal}",
            'status': 'publish',
            'meta': {
                'rfc': empleador.rfc,
                'direccion_fiscal': empleador.direccion_fiscal,
                'clabe': empleador.clabe,
                'banco': empleador.banco
            }
        }

        response = requests.post(
            f"{self.base_url}/wp-json/wp/v2/posts",
            json=data,
            auth=self.auth
        )

        if response.status_code == 201:
            return True, response.json()
        return False, response.json()

    def actualizar_oportunidad(self, oportunidad: Oportunidad, wp_id: int):
        """Actualiza una oportunidad en WordPress"""
        data = {
            'title': oportunidad.titulo,
            'content': oportunidad.descripcion,
            'meta': {
                'tipo_contrato': oportunidad.tipo_contrato,
                'salario_minimo': str(oportunidad.salario_minimo),
                'salario_maximo': str(oportunidad.salario_maximo),
                'pais': oportunidad.pais,
                'ciudad': oportunidad.ciudad,
                'modalidad': oportunidad.modalidad,
                'empleador_id': oportunidad.empleador.id
            }
        }

        response = requests.post(
            f"{self.base_url}/wp-json/wp/v2/posts/{wp_id}",
            json=data,
            auth=self.auth
        )

        if response.status_code == 200:
            return True, response.json()
        return False, response.json()

    def eliminar_oportunidad(self, wp_id: int):
        """Elimina una oportunidad de WordPress"""
        response = requests.delete(
            f"{self.base_url}/wp-json/wp/v2/posts/{wp_id}",
            auth=self.auth
        )

        if response.status_code == 200:
            return True, response.json()
        return False, response.json()
