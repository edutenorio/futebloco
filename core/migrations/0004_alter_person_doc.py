# Generated by Django 4.1.5 on 2023-12-26 22:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_alter_person_doc_alter_person_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='doc',
            field=models.CharField(blank=True, max_length=14, null=True, unique=True),
        ),
    ]
