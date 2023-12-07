# Generated by Django 3.2.18 on 2023-12-04 08:32

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('academic_year', '0001_initial'),
        ('term', '0001_initial'),
        ('classes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FeeStructure',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('instructions', models.CharField(blank=True, max_length=255, null=True)),
                ('fee_structure_values', models.JSONField(default=list, null=True)),
                ('school_id', models.UUIDField(blank=True, null=True)),
                ('academic_year', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='fee_structures', to='academic_year.academicyear')),
                ('classes', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='fee_structures', to='classes.classes')),
                ('term', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='fee_structures', to='term.term')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]