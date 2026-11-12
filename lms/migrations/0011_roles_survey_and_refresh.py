from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('lms', '0010_course_schedule_classroom_course_topic'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(model_name='student', name='job_position', field=models.CharField(blank=True, max_length=160, verbose_name='Position / job title')),
        migrations.AddField(model_name='student', name='skills_before', field=models.TextField(blank=True, verbose_name='Skills before training')),
        migrations.AddField(model_name='student', name='skills_after', field=models.TextField(blank=True, verbose_name='Skills after training')),
        migrations.AddField(model_name='instructor', name='user', field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='instructor_profile', to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name='course', name='revision_period_months', field=models.PositiveIntegerField(default=0, blank=True, help_text='Set 0 for no refresher requirement. For three years, enter 36.', verbose_name='Refresher interval (months)')),
        migrations.AddField(model_name='register', name='completed_on', field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name='examgrade', name='written_score', field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True, verbose_name='Written score')),
        migrations.AddField(model_name='examgrade', name='practical_score', field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True, verbose_name='Practical/project score')),
        migrations.CreateModel(name='SurveyQuestion', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('audience', models.CharField(choices=[('I', 'Instructor'), ('S', 'Student')], max_length=1)),
            ('title', models.CharField(max_length=320)),
            ('position', models.PositiveIntegerField(default=0)),
            ('active', models.BooleanField(default=True)),
        ], options={'ordering': ('audience', 'position', 'pk')}),
        migrations.CreateModel(name='SurveyResponse', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('audience', models.CharField(choices=[('I', 'Instructor'), ('S', 'Student')], max_length=1)),
            ('updated_at', models.DateTimeField(auto_now=True)),
            ('course', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='survey_responses', to='lms.course')),
            ('instructor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='survey_responses', to='lms.instructor')),
            ('register', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='survey_responses', to='lms.register')),
            ('recorded_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
        ], options={'constraints': [
            models.UniqueConstraint(fields=('course', 'instructor'), name='survey_unique_instructor_course'),
            models.UniqueConstraint(fields=('course', 'register'), name='survey_unique_register_course'),
        ]}),
        migrations.CreateModel(name='SurveyAnswer', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('rating', models.PositiveSmallIntegerField()),
            ('question', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='answers', to='lms.surveyquestion')),
            ('response', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='lms.surveyresponse')),
        ], options={'constraints': [models.UniqueConstraint(fields=('response', 'question'), name='survey_unique_answer')]}),
    ]
