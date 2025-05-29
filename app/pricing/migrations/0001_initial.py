"""
Migración inicial para la aplicación de precios.
"""
from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
import django.utils.timezone
import uuid
import django.core.validators
from django.db.models import Q


class Migration(migrations.Migration):
    """Migración inicial para la aplicación de precios."""

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DiscountCoupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=20, unique=True, verbose_name='Código')),
                ('discount_percentage', models.PositiveIntegerField(help_text='Porcentaje de descuento (0-100)', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)], verbose_name='Porcentaje de descuento')),
                ('description', models.TextField(blank=True, help_text='Descripción del cupón', null=True, verbose_name='Descripción')),
                ('is_used', models.BooleanField(default=False, verbose_name='¿Usado?')),
                ('used_at', models.DateTimeField(blank=True, null=True, verbose_name='Fecha de uso')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Fecha de actualización')),
                ('expiration_date', models.DateTimeField(help_text='Fecha de expiración del cupón', verbose_name='Fecha de expiración')),
                ('max_uses', models.PositiveIntegerField(default=1, help_text='Número máximo de usos permitidos', verbose_name='Usos máximos')),
                ('use_count', models.PositiveIntegerField(default=0, help_text='Número de veces que se ha utilizado', verbose_name='Contador de usos')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pricing_discount_coupons', to=settings.AUTH_USER_MODEL, verbose_name='Usuario', help_text='Usuario al que se le asigna el cupón')),
                ('proposal', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='discount_coupons', to='app.proposal', verbose_name='Propuesta')),
                ('description', models.TextField(blank=True, help_text='Descripción del cupón', null=True, verbose_name='Descripción')),
                ('max_uses', models.PositiveIntegerField(default=1, help_text='Número máximo de usos permitidos')),
                ('use_count', models.PositiveIntegerField(default=0, help_text='Número de veces que se ha usado el cupón')),
            ],
            options={
                'verbose_name': 'Cupón de descuento',
                'verbose_name_plural': 'Cupones de descuento',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PromotionBanner',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Título')),
                ('subtitle', models.CharField(blank=True, max_length=200, null=True, verbose_name='Subtítulo')),
                ('content', models.TextField(blank=True, null=True, verbose_name='Contenido')),
                ('image', models.ImageField(blank=True, null=True, upload_to='promotions/banners/', verbose_name='Imagen')),
                ('is_active', models.BooleanField(default=True, verbose_name='¿Activo?')),
                ('priority', models.IntegerField(default=0, help_text='Prioridad de visualización (mayor número = mayor prioridad)', verbose_name='Prioridad')),
                ('start_date', models.DateTimeField(help_text='Fecha y hora de inicio de la promoción', verbose_name='Fecha de inicio')),
                ('end_date', models.DateTimeField(help_text='Fecha y hora de finalización de la promoción', verbose_name='Fecha de finalización')),
                ('button_text', models.CharField(blank=True, max_length=50, null=True, verbose_name='Texto del botón')),
                ('target_url', models.URLField(blank=True, null=True, verbose_name='URL de destino')),
                ('badge_text', models.CharField(blank=True, max_length=50, null=True, verbose_name='Texto de la etiqueta')),
                ('badge_style', models.CharField(choices=[('primary', 'Primario'), ('secondary', 'Secundario'), ('success', 'Éxito'), ('danger', 'Peligro'), ('warning', 'Advertencia'), ('info', 'Informativo'), ('light', 'Claro'), ('dark', 'Oscuro')], default='primary', max_length=20, verbose_name='Estilo de la etiqueta')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
            ],
            options={
                'verbose_name': 'Banner promocional',
                'verbose_name_plural': 'Banners promocionales',
                'ordering': ['-priority', '-start_date'],
                'indexes': [
                    models.Index(fields=['is_active']),
                    models.Index(fields=['start_date', 'end_date']),
                ],
            },
        ),
        migrations.CreateModel(
            name='TeamEvaluation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('pending', 'Pendiente'), ('in_progress', 'En progreso'), ('completed', 'Completada'), ('expired', 'Expirada')], default='pending', max_length=20, verbose_name='Estado')),
                ('team_size', models.PositiveIntegerField(help_text='Número de miembros del equipo', verbose_name='Tamaño del equipo')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='Notas')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Fecha de actualización')),
                ('expires_at', models.DateTimeField(help_text='Fecha de expiración de la evaluación', verbose_name='Válido hasta')),
                ('discount_percentage', models.PositiveIntegerField(default=100, help_text='Porcentaje de descuento para la evaluación del equipo', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)], verbose_name='Porcentaje de descuento')),
                ('coupon', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='team_evaluation', to='pricing.discountcoupon', verbose_name='Cupón asociado')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='team_evaluations', to=settings.AUTH_USER_MODEL, verbose_name='Usuario')),
            ],
            options={
                'verbose_name': 'Evaluación de equipo',
                'verbose_name_plural': 'Evaluaciones de equipo',
                'ordering': ['-created_at'],
            },
        ),
    ]
