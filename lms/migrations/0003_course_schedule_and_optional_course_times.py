# Reconcile models.py with the SQLite schema supplied in the project archive.
# Existing courses do not have start/end time values, so no imaginary times are assigned.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('lms', '0002_rename_profile_image_instructor_profile_img_and_more')]

    operations = [
        migrations.AddField(
            model_name='course',
            name='start_time',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='course',
            name='end_time',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='CourseSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weekday', models.IntegerField(choices=[
                    (0, 'Saturday'), (1, 'Sunday'), (2, 'Monday'),
                    (3, 'Tuesday'), (4, 'Wednesday'), (5, 'Thursday'), (6, 'Friday'),
                ])),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                             related_name='schedules', to='lms.course')),
                ('instructor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                                 related_name='schedules', to='lms.instructor')),
            ],
        ),
    ]
