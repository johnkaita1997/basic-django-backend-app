# Generated by Django 3.2.18 on 2023-11-29 12:05

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('school', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AppUser',
            fields=[
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('date_deleted', models.DateTimeField(blank=True, null=True)),
                ('date_joined', models.DateTimeField(blank=True, null=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_agent', models.BooleanField(default=False)),
                ('is_superuser', models.BooleanField(default=False)),
                ('is_admin', models.BooleanField(default=False)),
                ('first_name', models.CharField(blank=True, max_length=255, null=True)),
                ('last_name', models.CharField(blank=True, max_length=255, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('username', models.CharField(blank=True, max_length=255, null=True)),
                ('email', models.CharField(max_length=255, unique=True)),
                ('password', models.CharField(blank=True, max_length=255, null=True)),
                ('confirmpassword', models.CharField(blank=True, max_length=255, null=True)),
                ('phone', models.CharField(blank=True, max_length=255, null=True)),
                ('location', models.CharField(blank=True, max_length=255, null=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('roles', models.ManyToManyField(blank=True, related_name='users', to='auth.Group')),
                ('school_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='school_id', to='school.school')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'ordering': ['-date_created'],
            },
        ),
    ]
