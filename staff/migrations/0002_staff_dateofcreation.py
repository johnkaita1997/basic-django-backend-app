# Generated by Django 3.2.18 on 2023-12-18 09:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('staff', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='staff',
            name='dateofcreation',
            field=models.DateField(auto_now_add=True, null=True),
        ),
    ]