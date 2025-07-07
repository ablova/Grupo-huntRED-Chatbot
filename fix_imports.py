#!/usr/bin/env python3
"""
Script para corregir las importaciones de modelos en archivos específicos.
"""

import os
import re

def fix_imports_in_file(file_path):
    """Corrige las importaciones en un archivo específico."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Actualizar importaciones específicas
        replacements = [
            # Gamification models
            (r'from app\.ats\.gamification\.models import ([^,\n]+)', r'from app.ats.models import \1'),
            
            # Pricing models - modelos que están en app.ats.models
            (r'from app\.ats\.pricing\.models import ([^,\n]*PaymentGateway[^,\n]*)', r'from app.ats.models import \1'),
            (r'from app\.ats\.pricing\.models import ([^,\n]*PaymentTransaction[^,\n]*)', r'from app.ats.models import \1'),
            (r'from app\.ats\.pricing\.models import ([^,\n]*BankAccount[^,\n]*)', r'from app.ats.models import \1'),
            (r'from app\.ats\.pricing\.models import ([^,\n]*ScheduledPayment[^,\n]*)', r'from app.ats.models import \1'),
            (r'from app\.ats\.pricing\.models import ([^,\n]*ScheduledPaymentExecution[^,\n]*)', r'from app.ats.models import \1'),
            (r'from app\.ats\.pricing\.models import ([^,\n]*PricingStrategy[^,\n]*)', r'from app.ats.models import \1'),
            (r'from app\.ats\.pricing\.models import ([^,\n]*DiscountRule[^,\n]*)', r'from app.ats.models import \1'),
            (r'from app\.ats\.pricing\.models import ([^,\n]*ReferralFee[^,\n]*)', r'from app.ats.models import \1'),
            (r'from app\.ats\.pricing\.models import ([^,\n]*Oportunidad[^,\n]*)', r'from app.ats.models import \1'),
            (r'from app\.ats\.pricing\.models import ([^,\n]*Empleador[^,\n]*)', r'from app.ats.models import \1'),
            (r'from app\.ats\.pricing\.models import ([^,\n]*SincronizacionError[^,\n]*)', r'from app.ats.models import \1'),
            (r'from app\.ats\.pricing\.models import ([^,\n]*SincronizacionLog[^,\n]*)', r'from app.ats.models import \1'),
            (r'from app\.ats\.pricing\.models import ([^,\n]*DiscountCoupon[^,\n]*)', r'from app.ats.models import \1'),
            
            # Modelos que están en app.models
            (r'from app\.ats\.pricing\.models import ([^,\n]*Service[^,\n]*)', r'from app.ats.models import \1'),
            (r'from app\.ats\.pricing\.models import ([^,\n]*Invoice[^,\n]*)', r'from app.ats.models import \1'),
            (r'from app\.ats\.pricing\.models import ([^,\n]*Order[^,\n]*)', r'from app.ats.models import \1'),
            (r'from app\.ats\.pricing\.models import ([^,\n]*Proposal[^,\n]*)', r'from app.ats.models import \1'),
        ]
        
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)
        
        # Si el contenido cambió, escribir el archivo
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed: {file_path}")
            return True
        
        return False
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

def main():
    """Función principal."""
    files_to_fix = [
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
    
    fixed_files = 0
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            if fix_imports_in_file(file_path):
                fixed_files += 1
    
    print(f"\nTotal files fixed: {fixed_files}")

if __name__ == "__main__":
    main() 