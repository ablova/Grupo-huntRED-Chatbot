#!/usr/bin/env python3
"""
Script para actualizar las importaciones de modelos en el proyecto.
"""

import os
import re
from pathlib import Path

def update_imports_in_file(file_path):
    """Actualiza las importaciones en un archivo específico."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Actualizar importaciones de gamification.models
        content = re.sub(
            r'from app\.ats\.gamification\.models import ([^,\n]+)',
            r'from app.ats.models import \1',
            content
        )
        
        # Actualizar importaciones de pricing.models (solo para modelos que están en app.models)
        content = re.sub(
            r'from app\.ats\.pricing\.models import ([^,\n]*DiscountCoupon[^,\n]*)',
            r'from app.ats.models import \1',
            content
        )
        
        # Si el contenido cambió, escribir el archivo
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated: {file_path}")
            return True
        
        return False
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False

def main():
    """Función principal."""
    project_root = Path(".")
    updated_files = 0
    
    # Archivos específicos que necesitan actualización
    files_to_update = [
        "app/ats/automation/assessment_triggers.py",
        "app/ats/pricing/services/payment_processing_service.py",
        "app/ats/pricing/services/unified_pricing_service.py",
        "app/ats/pricing/services/recommendation_service.py",
        "app/ats/pricing/views.py",
        "app/ats/pricing/services/integrations/wordpress_sync_service.py",
        "app/ats/pricing/services/billing_service.py",
        "app/ats/pricing/services/pricing_service.py",
        "app/ats/pricing/services/rewards_service.py",
        "app/ats/pricing/services/external_service_service.py",
        "app/ats/pricing/services/scheduled_payment_service.py",
        "app/ats/pricing/services/notification_service.py",
        "app/ats/pricing/gateways/banks/bbva.py",
        "app/ats/pricing/gateways/banks/base_bank_gateway.py",
        "app/ats/pricing/forms.py",
        "app/ats/pricing/integrations/automation/workflow_engine.py",
        "app/ats/pricing/proposal_renderer.py",
        "app/ats/pricing/integration_example.py",
        "app/ats/pricing/tasks.py",
        "app/ats/api/pricing_api.py",
        "app/ats/dashboard/views.py",
        "app/ats/feedback/signals.py",
        "app/ats/dashboard/super_admin_dashboard.py",
        "app/ats/admin/pricing/__init__.py",
        "app/ats/admin/pricing/unified_admin.py",
        "app/ats/referrals/tests.py"
    ]
    
    for file_path in files_to_update:
        if os.path.exists(file_path):
            if update_imports_in_file(file_path):
                updated_files += 1
    
    print(f"\nTotal files updated: {updated_files}")

if __name__ == "__main__":
    main() 