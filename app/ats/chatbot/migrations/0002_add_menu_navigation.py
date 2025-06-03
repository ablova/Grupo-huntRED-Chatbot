from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatstate',
            name='menu_page',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='chatstate',
            name='last_menu',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='chatstate',
            name='last_submenu',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='chatstate',
            name='search_term',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddIndex(
            model_name='chatstate',
            index=models.Index(fields=['menu_page'], name='chatbot_ch_menu_pa_123456_idx'),
        ),
        migrations.AddIndex(
            model_name='chatstate',
            index=models.Index(fields=['last_menu'], name='chatbot_ch_last_me_123456_idx'),
        ),
        migrations.AddIndex(
            model_name='chatstate',
            index=models.Index(fields=['last_submenu'], name='chatbot_ch_last_su_123456_idx'),
        ),
    ] 