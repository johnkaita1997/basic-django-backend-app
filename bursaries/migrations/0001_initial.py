# Generated by Django 3.2.18 on 2023-12-13 07:40

from django.db import migrations, models
import django.db.models.deletion
import utils
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('school', '0001_initial'),
        ('payment_methods', '0002_auto_20231206_1943'),
        ('bank_accounts', '0001_initial'),
        ('term', '0004_remove_term_year'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bursary',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('transactionNumber', models.CharField(max_length=255)),
                ('receipientAddress', models.CharField(blank=True, max_length=255, null=True)),
                ('institution', models.CharField(max_length=255)),
                ('institutionAddress', models.CharField(max_length=255)),
                ('bankAccount', models.ForeignKey(default=utils.currentAcademicYear, on_delete=django.db.models.deletion.CASCADE, related_name='bursaries', to='bank_accounts.bankaccount')),
                ('paymentMethod', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='bursaries', to='payment_methods.paymentmethod')),
                ('school_id', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='bursaries', to='school.school')),
                ('term', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='bursaries', to='term.term')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
