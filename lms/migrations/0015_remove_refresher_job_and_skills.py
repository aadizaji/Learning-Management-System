from django.db import migrations


def preserve_job_titles(apps, schema_editor):
    """Keep historical job text where the replacement Job Title is empty."""
    Student = apps.get_model('lms', 'Student')
    for student in Student.objects.filter(job_title='').exclude(job='').only('id', 'job', 'job_title').iterator():
        Student.objects.filter(pk=student.pk).update(job_title=student.job[:180])


class Migration(migrations.Migration):
    dependencies = [('lms', '0014_course_delivery_and_question_archive')]

    operations = [
        migrations.RunPython(preserve_job_titles, migrations.RunPython.noop),
        migrations.RemoveField(model_name='student', name='job'),
        migrations.RemoveField(model_name='student', name='skills_before'),
        migrations.RemoveField(model_name='student', name='skills_after'),
        migrations.RemoveField(model_name='course', name='revision_period_months'),
    ]
