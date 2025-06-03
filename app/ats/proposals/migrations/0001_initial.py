from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Proposal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pricing_total', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Total del Pricing')),
                ('pricing_details', models.JSONField(verbose_name='Detalles del Pricing')),
                ('status', models.CharField(choices=[('PENDING', 'Pendiente'), ('SENT', 'Enviada'), ('CONVERTED', 'Convertida'), ('REJECTED', 'Rechazada')], default='PENDING', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='proposals', to='app.person')),
                ('opportunity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='proposals', to='app.opportunity')),
                ('vacancies', models.ManyToManyField(related_name='proposals', to='app.vacancy')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
