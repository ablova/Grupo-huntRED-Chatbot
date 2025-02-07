# Ubicacion SEXSI -- /home/pablollh/app/sexsi/urls.py
from django.urls import path
from app.sexsi.views import (
    create_agreement, agreement_detail, sign_agreement, 
    download_pdf, upload_signature_and_selfie, finalize_agreement, request_revision, revoke_agreement
)

app_name = 'sexsi'

urlpatterns = [
    path('create/', create_agreement, name='create_agreement'),
    path('agreement/<int:agreement_id>/', agreement_detail, name='agreement_detail'),
    path('sign/<int:agreement_id>/<str:signer>/<uuid:token>/', sign_agreement, name='sign_agreement'),
    path('download/<int:agreement_id>/', download_pdf, name='download_pdf'),
    path('sign/save/<int:agreement_id>/', upload_signature_and_selfie, name='save_signature'),
    path('sign/finalize/<int:agreement_id>/<str:signer>/<uuid:token>/', finalize_agreement, name='finalize_agreement'),
    path('sign/revision/<int:agreement_id>/', request_revision, name='request_revision'),
    path('sign/revoke/<int:agreement_id>/', views.revoke_agreement, name='revoke_agreement'),

    # PAYPAL
    path('webhook/paypal/', views.paypal_webhook, name='paypal_webhook'),
]
