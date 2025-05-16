from django.shortcuts import render
from django.views import View
from app.services.email_generator import EmailGenerator
from app.models import Company

class SmartEmailView(View):
    def get(self, request, company_id):
        """Genera y muestra un correo inteligente"""
        company = Company.objects.get(id=company_id)
        email_generator = EmailGenerator(company_id)
        email_content = email_generator.generate_email()
        
        return render(request, 'proposals/smart_email_preview.html', {
            'email_content': email_content,
            'company': company
        })

    def post(self, request, company_id):
        """Envía el correo generado"""
        company = Company.objects.get(id=company_id)
        email_generator = EmailGenerator(company_id)
        email_content = email_generator.generate_email()
        
        # Aquí implementar el envío del correo
        # send_email(company, email_content)
        
        return render(request, 'proposals/smart_email_sent.html', {
            'company': company,
            'email_content': email_content
        })
