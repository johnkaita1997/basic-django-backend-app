# Generated by Django 3.2.18 on 2023-12-18 12:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment_in_kind_Receipt', '0004_pikreceipt_dateofcreation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pikreceipt',
            name='addition_notes',
            field=models.CharField(blank=True, max_length=7000, null=True),
        ),
    ]