# Generated by Django 3.2.18 on 2023-12-07 15:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0005_student_current_term'),
        ('academic_year', '0002_academicyear_is_current'),
        ('streams', '0001_initial'),
        ('classes', '0001_initial'),
        ('term', '0003_alter_term_year'),
        ('invoices', '0010_remove_invoice_isdeleted'),
    ]

    operations = [
        migrations.AddField(
            model_name='uninvoice',
            name='invoice_who',
            field=models.CharField(default='class', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='uninvoice',
            name='structure_stream',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='streams.stream'),
        ),
        migrations.AddField(
            model_name='uninvoice',
            name='student',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='innovation_document_creator', to='students.student'),
        ),
        migrations.AlterField(
            model_name='uninvoice',
            name='structure_class',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='classes.classes'),
        ),
        migrations.AlterField(
            model_name='uninvoice',
            name='structure_term',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='term.term'),
        ),
        migrations.AlterField(
            model_name='uninvoice',
            name='structure_year',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='academic_year.academicyear'),
        ),
    ]