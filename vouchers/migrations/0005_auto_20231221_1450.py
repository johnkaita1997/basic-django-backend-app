# Generated by Django 3.2.18 on 2023-12-21 11:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('suppliers', '0003_alter_supplier_notes'),
        ('staff', '0002_staff_dateofcreation'),
        ('vouchers', '0004_alter_voucher_description'),
    ]

    operations = [
        migrations.RenameField(
            model_name='voucher',
            old_name='member',
            new_name='other',
        ),
        migrations.AddField(
            model_name='voucher',
            name='staff',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='vouchers', to='staff.staff'),
        ),
        migrations.AddField(
            model_name='voucher',
            name='supplier',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='vouchers', to='suppliers.supplier'),
        ),
    ]
