"""Align Student model fields with existing SQLite database.

Existing Student records receive empty values for previously absent fields.
The empty value is an unknown value, not a fabricated job/workplace.
"""
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('lms', '0004_instructor_educational_certification'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='job',
            field=models.CharField(max_length=100, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='student',
            name='work_place',
            field=models.CharField(max_length=100, default=''),
            preserve_default=False,
        ),
    ]
