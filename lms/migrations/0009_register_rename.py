# Preserve data while renaming the former Enrollment model and relationship fields.
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('lms', '0008_exam_examgrade')]
    operations = [
        migrations.RenameModel(old_name='Enrollment', new_name='Register'),
        migrations.RenameField(model_name='register', old_name='enrollment_date', new_name='register_date'),
        migrations.RemoveConstraint(model_name='attendance', name='unique_session_enrollment'),
        migrations.RemoveConstraint(model_name='examgrade', name='unique_exam_enrollment'),
        migrations.RenameField(model_name='attendance', old_name='enrollment', new_name='register'),
        migrations.RenameField(model_name='examgrade', old_name='enrollment', new_name='register'),
        migrations.RenameField(model_name='certificate', old_name='enrollment', new_name='register'),
        migrations.AddConstraint(model_name='attendance', constraint=models.UniqueConstraint(fields=('session', 'register'), name='unique_session_register')),
        migrations.AddConstraint(model_name='examgrade', constraint=models.UniqueConstraint(fields=('exam', 'register'), name='unique_exam_register')),
        migrations.AlterModelOptions(name='attendance', options={'ordering': ['register__student__last_name', 'register__student__first_name']}),
        migrations.AlterModelOptions(name='examgrade', options={'ordering': ['register__student__last_name', 'register__student__first_name']}),
    ]
