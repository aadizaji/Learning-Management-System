from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('lms', '0009_register_rename')]
    operations = [
        migrations.AddField(
            model_name='courseschedule', name='classroom',
            field=models.CharField(blank=True, default='', max_length=30),
        ),
        migrations.CreateModel(
            name='CourseTopic',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=220)),
                ('position', models.PositiveIntegerField(default=0)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='topics', to='lms.course')),
            ],
            options={'ordering': ['position', 'pk']},
        ),
    ]
