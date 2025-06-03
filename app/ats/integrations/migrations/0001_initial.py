from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Integration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('type', models.CharField(choices=[('whatsapp', 'WhatsApp'), ('telegram', 'Telegram'), ('messenger', 'Messenger'), ('instagram', 'Instagram'), ('slack', 'Slack'), ('email', 'Email')], max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='IntegrationConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=100)),
                ('value', models.TextField()),
                ('is_secret', models.BooleanField(default=False)),
                ('integration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='configs', to='integrations.integration')),
            ],
        ),
    ] 