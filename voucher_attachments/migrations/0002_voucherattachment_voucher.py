# Generated by Django 3.2.18 on 2023-12-25 03:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('voucher_attachments', '0001_initial'),
        ('vouchers', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='voucherattachment',
            name='voucher',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='voucher_attachments', to='vouchers.voucher'),
        ),
    ]
