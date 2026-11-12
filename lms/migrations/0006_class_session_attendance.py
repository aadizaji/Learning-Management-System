# Attendance feature: actual course meetings and per-enrollment records.
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('lms', '0005_student_job_and_work_place')]

    operations = [
        migrations.CreateModel(
            name='ClassSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('status', models.CharField(max_length=1, choices=[('S', 'Scheduled'), ('C', 'Completed'), ('X', 'Cancelled')], default='S')),
                ('cancellation_reason', models.TextField(blank=True)),
                ('course_schedule', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sessions', to='lms.courseschedule')),
            ],
            options={
                'ordering': ['date', 'start_time', 'pk'],
            },
        ),
        migrations.AddConstraint(
            model_name='classsession',
            constraint=models.UniqueConstraint(fields=('course_schedule', 'date'), name='unique_course_schedule_date'),
        ),
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('P', 'Present'), ('A', 'Absent')], max_length=1)),
                ('recorded_at', models.DateTimeField(auto_now=True)),
                ('enrollment', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='attendance_records', to='lms.enrollment')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='attendance_records', to='lms.classsession')),
            ],
            options={'ordering': ['enrollment__student__last_name', 'enrollment__student__first_name']},
        ),
        migrations.AddConstraint(
            model_name='attendance',
            constraint=models.UniqueConstraint(fields=('session', 'enrollment'), name='unique_session_enrollment'),
        ),
    ]
