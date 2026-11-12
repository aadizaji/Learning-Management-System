# Exam management and grade tracking, without an online quiz engine.
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('lms', '0007_certificate')]

    operations = [
        migrations.CreateModel(
            name='Exam',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=160)),
                ('exam_type', models.CharField(choices=[('O', 'Online'), ('F', 'Offline')], default='F', max_length=1)),
                ('exam_date', models.DateField()),
                ('max_score', models.DecimalField(decimal_places=2, default=100, max_digits=6)),
                ('passing_score', models.DecimalField(decimal_places=2, default=70, max_digits=6)),
                ('description', models.TextField(blank=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='exams', to='lms.course')),
            ],
            options={'ordering': ['-exam_date', '-pk']},
        ),
        migrations.CreateModel(
            name='ExamGrade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.DecimalField(decimal_places=2, max_digits=6)),
                ('recorded_at', models.DateTimeField(auto_now=True)),
                ('enrollment', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='exam_grades', to='lms.enrollment')),
                ('exam', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grades', to='lms.exam')),
            ],
            options={'ordering': ['enrollment__student__last_name', 'enrollment__student__first_name']},
        ),
        migrations.AddConstraint(
            model_name='examgrade',
            constraint=models.UniqueConstraint(fields=('exam', 'enrollment'), name='unique_exam_enrollment'),
        ),
    ]
