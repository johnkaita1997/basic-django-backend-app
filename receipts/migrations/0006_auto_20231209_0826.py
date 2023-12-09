# Generated by Django 3.2.18 on 2023-12-09 05:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('term', '0003_alter_term_year'),
        ('currencies', '0002_alter_currency_currency_code'),
        ('academic_year', '0002_academicyear_is_current'),
        ('receipts', '0005_auto_20231209_0812'),
    ]

    operations = [
        migrations.AddField(
            model_name='receipt',
            name='currency',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='receipts', to='currencies.currency'),
        ),
        migrations.AddField(
            model_name='receipt',
            name='term',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='receipts', to='term.term'),
        ),
        migrations.AddField(
            model_name='receipt',
            name='year',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='receipts', to='academic_year.academicyear'),
        ),
    ]
