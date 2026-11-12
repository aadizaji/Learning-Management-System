from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('lms', '0011_roles_survey_and_refresh'),
    ]

    operations = [
        migrations.RenameField(
            model_name='student', old_name='job_position', new_name='job_title',
        ),
        migrations.AlterField(
            model_name='student', name='job_title',
            field=models.TextField(blank=True, verbose_name='Job title'),
        ),
        migrations.AddField(
            model_name='student', name='organizational_position',
            field=models.CharField(
                blank=True, max_length=16, verbose_name='Organizational position',
                choices=[
                    ('employee', 'Employee'), ('worker', 'Worker'),
                    ('associate', 'Technical associate'), ('technician', 'Technician'),
                    ('specialist', 'Specialist'), ('officer', 'Officer'),
                    ('head', 'Head'), ('manager', 'Manager'),
                    ('ceo', 'CEO'), ('other', 'Other'),
                ],
            ),
        ),
        migrations.AddField(
            model_name='student', name='educational_certification',
            field=models.CharField(
                blank=True, max_length=1, verbose_name='Educational Certification',
                choices=[('D', 'Diploma'), ('A', 'Associate degree'),
                         ('B', 'Bachelor'), ('M', 'Master'), ('P', 'Ph.D')],
            ),
        ),
        migrations.AlterField(
            model_name='instructor', name='educational_certification',
            field=models.CharField(
                choices=[('D', 'Diploma'), ('A', 'Associate degree'),
                         ('B', 'Bachelor'), ('M', 'Master'), ('P', 'Ph.D')],
                max_length=1,
            ),
        ),
    ]
