# Generated by Django 3.2.18 on 2023-12-09 06:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('payment_in_kind_Receipt', '0001_initial'),
        ('payment_in_kinds', '0002_alter_paymentinkind_quantity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paymentinkind',
            name='receipt',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='paymentinkinds', to='payment_in_kind_Receipt.pikreceipt'),
        ),
    ]
