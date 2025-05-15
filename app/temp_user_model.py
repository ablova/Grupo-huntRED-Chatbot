from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user


class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(max_length=20, choices=[
        ('SUPER_ADMIN', 'Super Administrador'),
        ('BU_COMPLETE', 'Consultor BU Completo'),
        ('BU_DIVISION', 'Consultor BU División')
    ], default='BU_DIVISION')
    status = models.CharField(max_length=20, choices=[
        ('ACTIVE', 'Activo'),
        ('INACTIVE', 'Inactivo'),
        ('PENDING_APPROVAL', 'Pendiente de Aprobación')
    ], default='PENDING_APPROVAL')
    verification_status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pendiente'),
        ('APPROVED', 'Aprobado'),
        ('REJECTED', 'Rechazado')
    ], default='PENDING')
    business_unit = models.ForeignKey(
        'BusinessUnit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        app_label = 'app'
        db_table = 'app_customuser'

    def __str__(self):
        return self.email
