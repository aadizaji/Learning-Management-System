# Add the Instructor field that exists in models.py but was missing from
# the original database and from migrations 0001-0003.
# Older instructor records receive an empty (unknown) value rather than
# an invented educational qualification.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('lms', '0003_course_schedule_and_optional_course_times'),
    ]

    operations = [
        migrations.AddField(
            model_name='instructor',
            name='educational_certification',
            field=models.CharField(
                choices=[
                    ('D', 'Diploma'),
                    ('B', 'Bachelor'),
                    ('M', 'Master'),
                    ('P', 'Ph.D'),
                ],
                max_length=1,
                default='',
            ),
            preserve_default=False,
        ),
    ]
