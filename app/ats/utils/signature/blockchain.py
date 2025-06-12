"""
Módulo para la integración con blockchain en el sistema de firmas.
"""
import hashlib
import json
import time
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BlockchainSignature:
    """
    Implementación de blockchain para trazabilidad de firmas.
    """
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()
        self.difficulty = 4  # Dificultad de minado

    def create_block(self, proof: int, previous_hash: Optional[str] = None) -> Dict:
        """
        Crea un nuevo bloque en la cadena.
        
        Args:
            proof: Prueba de trabajo
            previous_hash: Hash del bloque anterior
            
        Returns:
            Diccionario con la información del bloque
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash_block(self.chain[-1]) if self.chain else None
        }

        # Limpiar transacciones actuales
        self.current_transactions = []
        
        # Agregar bloque a la cadena
        self.chain.append(block)
        
        return block

    def add_signature_transaction(self, signature_data: Dict) -> int:
        """
        Agrega una transacción de firma al bloque actual.
        
        Args:
            signature_data: Datos de la firma
            
        Returns:
            Índice del bloque que contendrá la transacción
        """
        self.current_transactions.append({
            'type': 'signature',
            'data': signature_data,
            'timestamp': time.time()
        })
        
        return self.last_block['index'] + 1 if self.chain else 1

    def proof_of_work(self, last_proof: int) -> int:
        """
        Algoritmo simple de prueba de trabajo.
        
        Args:
            last_proof: Prueba anterior
            
        Returns:
            Nueva prueba
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    def valid_proof(self, last_proof: int, proof: int) -> bool:
        """
        Valida la prueba de trabajo.
        
        Args:
            last_proof: Prueba anterior
            proof: Prueba actual
            
        Returns:
            True si la prueba es válida
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:self.difficulty] == '0' * self.difficulty

    @staticmethod
    def hash_block(block: Dict) -> str:
        """
        Crea un hash SHA-256 de un bloque.
        
        Args:
            block: Bloque a hashear
            
        Returns:
            Hash del bloque
        """
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self) -> Dict:
        """Obtiene el último bloque de la cadena."""
        return self.chain[-1]

    def is_active(self) -> bool:
        """Verifica si la blockchain está activa."""
        return len(self.chain) > 0

    def get_last_block(self) -> Dict:
        """Obtiene el último bloque."""
        return self.last_block if self.chain else {}

    def get_total_transactions(self) -> int:
        """Obtiene el total de transacciones."""
        return sum(len(block['transactions']) for block in self.chain)

    def verify_signature(self, signature_id: str) -> bool:
        """
        Verifica la autenticidad de una firma en la blockchain.
        
        Args:
            signature_id: ID de la firma a verificar
            
        Returns:
            True si la firma es auténtica
        """
        for block in self.chain:
            for transaction in block['transactions']:
                if (transaction['type'] == 'signature' and 
                    transaction['data'].get('signature_id') == signature_id):
                    return True
        return False

    def get_signature_history(self, signature_id: str) -> List[Dict]:
        """
        Obtiene el historial de una firma en la blockchain.
        
        Args:
            signature_id: ID de la firma
            
        Returns:
            Lista de transacciones relacionadas con la firma
        """
        history = []
        for block in self.chain:
            for transaction in block['transactions']:
                if (transaction['type'] == 'signature' and 
                    transaction['data'].get('signature_id') == signature_id):
                    history.append({
                        'block_index': block['index'],
                        'timestamp': datetime.fromtimestamp(block['timestamp']).isoformat(),
                        'transaction': transaction
                    })
        return history

    def add_node(self, address: str) -> None:
        """
        Agrega un nuevo nodo a la lista de nodos.
        
        Args:
            address: Dirección del nodo
        """
        self.nodes.add(address)

    def get_nodes(self) -> set:
        """Obtiene la lista de nodos."""
        return self.nodes

    def resolve_conflicts(self) -> bool:
        """
        Resuelve conflictos entre nodos.
        
        Returns:
            True si la cadena fue reemplazada
        """
        neighbours = self.nodes
        new_chain = None
        max_length = len(self.chain)

        for node in neighbours:
            try:
                response = requests.get(f'{node}/chain')
                if response.status_code == 200:
                    length = response.json()['length']
                    chain = response.json()['chain']

                    if length > max_length and self.valid_chain(chain):
                        max_length = length
                        new_chain = chain
            except Exception as e:
                logger.error(f"Error al resolver conflictos con nodo {node}: {str(e)}")
                continue

        if new_chain:
            self.chain = new_chain
            return True

        return False

    def valid_chain(self, chain: List[Dict]) -> bool:
        """
        Verifica si una cadena es válida.
        
        Args:
            chain: Cadena a verificar
            
        Returns:
            True si la cadena es válida
        """
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            
            # Verificar que el hash del bloque anterior sea correcto
            if block['previous_hash'] != self.hash_block(last_block):
                return False

            # Verificar la prueba de trabajo
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

        return True 