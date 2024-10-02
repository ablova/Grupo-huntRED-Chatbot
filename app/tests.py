# /home/amigro/app/tests.py

from django.test import TestCase
from .models import FlowModel
from django.urls import reverse
import json

class FlowModelTest(TestCase):
    def setUp(self):
        self.flow = FlowModel.objects.create(
            name='Flujo de Prueba',
            description='Descripción del flujo de prueba',
            flow_data_json=json.dumps({
                'nodes': [
                    {'key': 'node1', 'text': 'Inicio', 'type': 'text', 'fill': 'lightblue'},
                    {'key': 'node2', 'text': 'Pregunta 1', 'type': 'text', 'fill': 'lightblue'}
                ],
                'links': [
                    {'key': 'link1', 'from': 'node1', 'to': 'node2', 'text': 'Sí'}
                ]
            })
        )

    def test_load_flow(self):
        response = self.client.get(reverse('admin:load_flow') + f'?flowmodel_id={self.flow.id}')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('nodes', data)
        self.assertIn('links', data)
        self.assertEqual(len(data['nodes']), 2)
        self.assertEqual(len(data['links']), 1)

    def test_save_flow(self):
        new_flow_data = {
            'flowmodel_id': self.flow.id,
            'nodes': [
                {'key': 'node1', 'text': 'Inicio', 'type': 'text', 'fill': 'lightblue'},
                {'key': 'node2', 'text': 'Pregunta 1 Actualizada', 'type': 'text', 'fill': 'lightblue'}
            ],
            'links': [
                {'key': 'link1', 'from': 'node1', 'to': 'node2', 'text': 'No'}
            ]
        }
        response = self.client.post(reverse('admin:save_flow'), data=json.dumps(new_flow_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.flow.refresh_from_db()
        updated_flow = json.loads(self.flow.flow_data_json)
        self.assertEqual(updated_flow['nodes'][1]['text'], 'Pregunta 1 Actualizada')
        self.assertEqual(updated_flow['links'][0]['text'], 'No')
