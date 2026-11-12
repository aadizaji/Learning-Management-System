from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('lms', '0013_manager_role_and_job_title')]

    operations = [
        migrations.AddField(
            model_name='course', name='delivery_mode',
            field=models.CharField(
                max_length=1, default='P', verbose_name='Delivery mode',
                choices=[('P', 'In person'), ('R', 'Remote'), ('H', 'In person and remote')],
            ),
        ),
        migrations.AddField(
            model_name='surveyquestion', name='archived',
            field=models.BooleanField(default=False),
        ),
    ]
