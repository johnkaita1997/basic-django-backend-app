# Generated by Django 3.2.18 on 2023-12-07 11:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0008_invoice_votehead'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='isDeleted',
            field=models.BooleanField(default=False),
        ),
    ]