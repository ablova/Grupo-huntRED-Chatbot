# /home/pablo/app/ats/pricing/migrations/0001_initial.py
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
                ('proposal', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='discount_coupons', to='app.Proposal', verbose_name='Propuesta')),
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
                    models.Index(fields=['is_active'], name='pricing_promotionalbanner_is_active_idx'),
                    models.Index(fields=['start_date', 'end_date'], name='pricing_promotionalbanner_dates_idx'),
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
        migrations.CreateModel(
            name='PricingStrategy',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('business_unit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.businessunit')),
            ],
            options={
                'verbose_name': 'Estrategia de Pricing',
                'verbose_name_plural': 'Estrategias de Pricing',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PricePoint',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('service_type', models.CharField(max_length=50)),
                ('base_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('currency', models.CharField(max_length=3)),
                ('min_duration', models.IntegerField(default=1)),
                ('max_duration', models.IntegerField(null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('strategy', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pricing.pricingstrategy')),
            ],
            options={
                'verbose_name': 'Punto de Precio',
                'verbose_name_plural': 'Puntos de Precio',
                'ordering': ['service_type', 'base_price'],
            },
        ),
        migrations.CreateModel(
            name='DiscountRule',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('service_type', models.CharField(max_length=50)),
                ('discount_type', models.CharField(max_length=20)),
                ('discount_value', models.DecimalField(decimal_places=2, max_digits=10)),
                ('min_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('max_amount', models.DecimalField(decimal_places=2, max_digits=10, null=True)),
                ('active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('strategy', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pricing.pricingstrategy')),
            ],
            options={
                'verbose_name': 'Regla de Descuento',
                'verbose_name_plural': 'Reglas de Descuento',
                'ordering': ['service_type', 'min_amount'],
            },
        ),
        migrations.CreateModel(
            name='ReferralFee',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('service_type', models.CharField(max_length=50)),
                ('fee_type', models.CharField(max_length=20)),
                ('fee_value', models.DecimalField(decimal_places=2, max_digits=10)),
                ('min_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('max_amount', models.DecimalField(decimal_places=2, max_digits=10, null=True)),
                ('active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('strategy', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pricing.pricingstrategy')),
            ],
            options={
                'verbose_name': 'Comisión por Referido',
                'verbose_name_plural': 'Comisiones por Referidos',
                'ordering': ['service_type', 'min_amount'],
            },
        ),
        migrations.CreateModel(
            name='PricingCalculation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('service_type', models.CharField(max_length=50)),
                ('base_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('discounts', models.DecimalField(decimal_places=2, max_digits=10, default=0)),
                ('referral_fees', models.DecimalField(decimal_places=2, max_digits=10, default=0)),
                ('total', models.DecimalField(decimal_places=2, max_digits=10)),
                ('currency', models.CharField(max_length=3)),
                ('metadata', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('business_unit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.businessunit')),
            ],
            options={
                'verbose_name': 'Cálculo de Precio',
                'verbose_name_plural': 'Cálculos de Precio',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PricingPayment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('estado', models.CharField(max_length=20)),
                ('monto', models.DecimalField(decimal_places=2, max_digits=10)),
                ('moneda', models.CharField(max_length=3)),
                ('metodo', models.CharField(max_length=50)),
                ('id_transaccion', models.CharField(max_length=100, null=True)),
                ('metadata', models.JSONField(default=dict)),
                ('fecha_creacion', models.DateTimeField(default=django.utils.timezone.now)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('calculo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pricing.pricingcalculation')),
            ],
            options={
                'verbose_name': 'Pago',
                'verbose_name_plural': 'Pagos',
                'ordering': ['-fecha_creacion'],
            },
        ),
        migrations.CreateModel(
            name='PricingProposal',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('estado', models.CharField(max_length=20)),
                ('titulo', models.CharField(max_length=200)),
                ('descripcion', models.TextField()),
                ('monto_total', models.DecimalField(decimal_places=2, max_digits=10)),
                ('moneda', models.CharField(max_length=3)),
                ('fecha_creacion', models.DateTimeField(default=django.utils.timezone.now)),
                ('fecha_envio', models.DateTimeField(null=True)),
                ('fecha_aprobacion', models.DateTimeField(null=True)),
                ('fecha_rechazo', models.DateTimeField(null=True)),
                ('metadata', models.JSONField(default=dict)),
                ('oportunidad', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.opportunity')),
            ],
            options={
                'verbose_name': 'Propuesta de Servicio',
                'verbose_name_plural': 'Propuestas de Servicio',
                'ordering': ['-fecha_creacion'],
            },
        ),
        migrations.CreateModel(
            name='ProposalSection',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tipo', models.CharField(max_length=50)),
                ('titulo', models.CharField(max_length=200)),
                ('contenido', models.TextField()),
                ('orden', models.IntegerField(default=0)),
                ('metadata', models.JSONField(default=dict)),
                ('propuesta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pricing.pricingproposal')),
            ],
            options={
                'verbose_name': 'Sección de Propuesta',
                'verbose_name_plural': 'Secciones de Propuesta',
                'ordering': ['propuesta', 'orden'],
            },
        ),
        migrations.CreateModel(
            name='ProposalTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('nombre', models.CharField(max_length=100)),
                ('descripcion', models.TextField(blank=True)),
                ('activo', models.BooleanField(default=True)),
                ('secciones', models.JSONField(default=list)),
                ('metadata', models.JSONField(default=dict)),
                ('fecha_creacion', models.DateTimeField(default=django.utils.timezone.now)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('business_unit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.businessunit')),
            ],
            options={
                'verbose_name': 'Plantilla de Propuesta',
                'verbose_name_plural': 'Plantillas de Propuesta',
                'ordering': ['-fecha_creacion'],
            },
        ),
    ]
