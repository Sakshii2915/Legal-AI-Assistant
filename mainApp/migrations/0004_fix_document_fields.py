# Generated manually

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainApp', '0003_add_chat_models'),
    ]

    operations = [
        # Remove old fields
        migrations.RemoveField(
            model_name='document',
            name='title',
        ),
        migrations.RemoveField(
            model_name='document',
            name='content',
        ),
        # Add new fields
        migrations.AddField(
            model_name='document',
            name='file',
            field=models.FileField(default='', upload_to='documents/'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='document',
            name='extracted_text',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
    ]
