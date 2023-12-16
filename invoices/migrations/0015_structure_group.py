# Generated by Django 3.2.18 on 2023-12-16 03:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('schoolgroups', '0002_alter_schoolgroup_school_id'),
        ('invoices', '0014_alter_invoice_invoiceno'),
    ]

    operations = [
        migrations.AddField(
            model_name='structure',
            name='group',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='structures', to='schoolgroups.schoolgroup'),
        ),
    ]
