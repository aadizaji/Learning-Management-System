from django.apps import AppConfig
from django.db.models.signals import post_migrate


def configure_access_groups(sender, **kwargs):
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType
    from django.apps import apps

    lms_config = apps.get_app_config('lms')
    for name in ('Manager', 'Instructor'):
        group, _ = Group.objects.get_or_create(name=name)
        allowed = []
        for model in lms_config.get_models():
            content_type = ContentType.objects.get_for_model(model)
            perms = Permission.objects.filter(content_type=content_type)
            if name == 'Manager':
                allowed.extend(perms)
            else:
                readable = {'student', 'instructor', 'course', 'coursecategory', 'register',
                            'courseschedule', 'coursetopic', 'classsession', 'attendance',
                            'exam', 'examgrade', 'surveyquestion', 'surveyresponse', 'surveyanswer'}
                editable = {'attendance', 'examgrade', 'surveyresponse', 'surveyanswer'}
                model_name = model._meta.model_name
                if model_name in readable:
                    allowed.extend(p for p in perms if p.codename == f'view_{model_name}' or
                                   (model_name in editable and p.codename in
                                    {f'add_{model_name}', f'change_{model_name}', f'delete_{model_name}'}))
        group.permissions.set(allowed)


class LmsConfig(AppConfig):
    name = 'lms'

    def ready(self):
        post_migrate.connect(configure_access_groups, sender=self, dispatch_uid='sematec_group_setup')
