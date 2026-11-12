"""Backfill actual sessions for courses that existed before this feature."""
from django.core.management.base import BaseCommand
from lms.models import Course
from lms.services.session_generator import generate_course_sessions


class Command(BaseCommand):
    help = 'Create any missing ClassSession rows for existing weekly schedules.'

    def handle(self, *args, **options):
        total_created, total_existing = 0, 0
        courses = Course.objects.prefetch_related('schedules').order_by('pk')
        for course in courses:
            result = generate_course_sessions(course)
            total_created += result['created']
            total_existing += result['existing']
        self.stdout.write(self.style.SUCCESS(
            f'Sessions: {total_created} created, {total_existing} already existed.'
        ))
