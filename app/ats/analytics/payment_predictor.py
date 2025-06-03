from sklearn.ensemble import RandomForestClassifier
import numpy as np
from app.models import Payment

class PaymentPredictor:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100)
        self.features = [
            'payment_history',
            'amount',
            'business_unit',
            'industry',
            'location',
            'payment_terms'
        ]
        
    def prepare_data(self, opportunity):
        """Prepara los datos para la predicción."""
        data = {
            'payment_history': opportunity.company.payment_history,
            'amount': opportunity.amount,
            'business_unit': opportunity.business_unit.payment_terms,
            'industry': opportunity.industry,
            'location': opportunity.location,
            'payment_terms': opportunity.payment_terms
        }
        return np.array([data[feature] for feature in self.features])
        
    def predict_payment(self, opportunity):
        """
        Predice la probabilidad de pago.
        
        Args:
            opportunity: Oportunidad
            
        Returns:
            Dict con la predicción
        """
        try:
            features = self.prepare_data(opportunity)
            probability = self.model.predict_proba([features])[0][1]
            
            return {
                'probability': probability,
                'status': 'likely' if probability > 0.7 else 'unlikely',
                'confidence': probability if probability > 0.7 else 1 - probability
            }
        except Exception as e:
            return {
                'error': str(e),
                'status': 'unknown',
                'confidence': 0.5
            }
