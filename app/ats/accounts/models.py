# app/ats/accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import RegexValidator
from django.conf import settings


class CustomUserManager(BaseUserManager):
    """
    Manager personalizado para el modelo CustomUser.
    """
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Crea y guarda un usuario con el email y contraseña proporcionados.
        """
        if not email:
            raise ValueError(_('El email es obligatorio'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Crea y guarda un usuario regular con el email y contraseña dados."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Crea y guarda un superusuario con el email y contraseña dados."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de usuario personalizado que utiliza email como identificador único.
    """
    email = models.EmailField(
        _('email address'),
        unique=True,
        error_messages={
            'unique': _("Ya existe un usuario con este email.")
        }
    )
    first_name = models.CharField(_('nombres'), max_length=150, blank=True)
    last_name = models.CharField(_('apellidos'), max_length=150, blank=True)
    
    # Campos de control
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designa si el usuario puede iniciar sesión en el sitio de administración.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designa si este usuario debe ser tratado como activo. '
            'Desmarque esta opción en lugar de borrar la cuenta.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    last_login = models.DateTimeField(_('last login'), blank=True, null=True)

    # Campos adicionales para consultores
    phone = models.CharField(_('teléfono'), max_length=20, blank=True, null=True)
    
    # Estados y verificación
    STATUS_CHOICES = [
        ('ACTIVE', _('Activo')),
        ('INACTIVE', _('Inactivo')),
        ('SUSPENDED', _('Suspendido')),
        ('PENDING', _('Pendiente')),
    ]
    status = models.CharField(
        _('estado'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE'
    )
    
    VERIFICATION_STATUS_CHOICES = [
        ('VERIFIED', _('Verificado')),
        ('UNVERIFIED', _('No verificado')),
        ('PENDING', _('Pendiente')),
        ('REJECTED', _('Rechazado')),
    ]
    verification_status = models.CharField(
        _('estado de verificación'),
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default='UNVERIFIED'
    )
    
    # Relaciones
    business_units = models.ManyToManyField(
        'app.BusinessUnit',
        verbose_name=_('unidades de negocio'),
        related_name='users',
        blank=True,
        help_text=_('Unidades de negocio a las que tiene acceso este usuario')
    )
    business_unit = models.ForeignKey(
        'app.BusinessUnit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('unidad de negocio principal'),
        related_name='primary_users'
    )
    division = models.ForeignKey(
        'app.Division',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('división'),
        related_name='users'
    )
    
    # Roles y permisos
    ROLE_CHOICES = [
        ('SUPER_ADMIN', _('Super Admin')),
        ('BU_ADMIN', _('Business Unit Admin')),
        ('BU_DIVISION', _('Business Unit Division')),
    ]
    role = models.CharField(
        _('rol'),
        max_length=20,
        choices=ROLE_CHOICES,
        default='BU_DIVISION'
    )
    permissions = models.JSONField(
        _('permisos'),
        default=dict,
        blank=True
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('usuario')
        verbose_name_plural = _('usuarios')
        db_table = 'auth_user'

    def __str__(self):
        return self.email

    def get_full_name(self):
        """Devuelve el nombre completo del usuario."""
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip()

    def get_short_name(self):
        """Devuelve el nombre corto del usuario (solo el primer nombre)."""
        return self.first_name

    def has_perm(self, perm, obj=None):
        """¿Tiene el usuario un permiso específico?"""
        return True

    def has_module_perms(self, app_label):
        """¿Tiene el usuario permisos para ver la aplicación `app_label`?"""
        return True

    @property
    def is_consultant(self):
        """¿Es el usuario un consultor?"""
        return hasattr(self, 'consultantprofile')

    @property
    def is_executive(self):
        """¿Es el usuario un ejecutivo?"""
        return hasattr(self, 'executiveprofile')
