# Generated for the Sematec LMS certificate-issuing feature.
import datetime
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('lms', '0006_class_session_attendance')]

    operations = [
        migrations.CreateModel(
            name='Certificate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('serial_number', models.CharField(max_length=40, unique=True)),
                ('grade', models.DecimalField(decimal_places=2, max_digits=5)),
                ('issue_date', models.DateField(default=datetime.date.today)),
                ('student_name', models.CharField(max_length=220)),
                ('course_title', models.CharField(max_length=220)),
                ('course_hours', models.PositiveIntegerField()),
                ('student_name_fa', models.CharField(blank=True, max_length=220)),
                ('course_title_fa', models.CharField(blank=True, max_length=220)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('enrollment', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='certificate', to='lms.enrollment')),
            ],
            options={'ordering': ['-issue_date', '-pk']},
        ),
    ]
