# Ubicación: /home/pablollh/app/sexsi/urls.py

from django.urls import path
from app.sexsi.views import (
    create_agreement, agreement_detail, sign_agreement, 
    download_pdf, upload_signature_and_selfie
)
from app.sexsi.biometric_auth import save_biometric_signature  # 🔹 Importa la función


app_name = 'sexsi'

urlpatterns = [
    path('create/', create_agreement, name='create_agreement'),
    path('agreement/<int:agreement_id>/', agreement_detail, name='agreement_detail'),
    path('sign/<int:agreement_id>/<str:signer>/<uuid:token>/', sign_agreement, name='sign_agreement'),
    path('download/<int:agreement_id>/', download_pdf, name='download_pdf'),
    path('sign/save/<int:agreement_id>/', upload_signature_and_selfie, name='save_signature'),  # 🔹 Quitamos <str:signer> y <uuid:token>
    path('sign/biometric/<int:agreement_id>/', save_biometric_signature, name='save_biometric_signature'),  # 🔹 Nueva ruta

]