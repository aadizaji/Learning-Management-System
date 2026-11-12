from django.db import migrations, models


def migrate_legacy_manager_role(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    User = apps.get_model('auth', 'User')
    manager, _ = Group.objects.using(schema_editor.connection.alias).get_or_create(name='Manager')
    Group.objects.using(schema_editor.connection.alias).get_or_create(name='Instructor')
    legacy = Group.objects.using(schema_editor.connection.alias).filter(name='Education Manager').first()
    if legacy:
        # Preserve every historical manager user before removing the old role.
        through = User.groups.through
        for user_id in through.objects.using(schema_editor.connection.alias).filter(group_id=legacy.pk).values_list('user_id', flat=True):
            through.objects.using(schema_editor.connection.alias).get_or_create(user_id=user_id, group_id=manager.pk)
        legacy.delete()


def reverse_roles(apps, schema_editor):
    # Preserve current role assignments on rollback; never silently revoke access.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('lms', '0012_student_job_organization_and_education'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]
    operations = [
        migrations.AlterField(
            model_name='student', name='job_title',
            field=models.CharField(max_length=180, blank=True, verbose_name='Job title'),
        ),
        migrations.RunPython(migrate_legacy_manager_role, reverse_roles),
    ]
