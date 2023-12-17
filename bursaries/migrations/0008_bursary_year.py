# Generated by Django 3.2.18 on 2023-12-17 03:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('academic_year', '0002_academicyear_is_current'),
        ('bursaries', '0007_alter_bursary_posted'),
    ]

    operations = [
        migrations.AddField(
            model_name='bursary',
            name='year',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='bursaries', to='academic_year.academicyear'),
        ),
    ]
