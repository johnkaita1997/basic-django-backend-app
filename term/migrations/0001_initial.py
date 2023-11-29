# Generated by Django 3.2.18 on 2023-11-29 12:05

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Term',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('term_name', models.CharField(max_length=255)),
                ('year', models.CharField(max_length=255)),
                ('begin_date', models.DateField()),
                ('end_date', models.DateField()),
                ('school_id', models.UUIDField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
