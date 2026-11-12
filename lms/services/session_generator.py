"""Create missing dated meetings from weekly slots, without editing existing history."""
from datetime import timedelta

from django.db import transaction

from lms.models import ClassSession


@transaction.atomic
def generate_course_sessions(course):
    if not course.pk:
        raise ValueError('Save the course before generating sessions.')
    if not course.start_date or not course.end_date or course.start_date > course.end_date:
        raise ValueError('A valid course start/end date range is required.')

    created_count = 0
    existing_count = 0
    for slot in course.schedules.all():
        if slot.start_time >= slot.end_time:
            raise ValueError(f'Invalid time range on schedule {slot.pk}.')
        # Python weekday(): Monday=0; LMS weekday: Saturday=0.
        project_weekday = (course.start_date.weekday() + 2) % 7
        offset = (slot.weekday - project_weekday) % 7
        meeting_day = course.start_date + timedelta(days=offset)

        while meeting_day <= course.end_date:
            _, created = ClassSession.objects.get_or_create(
                course_schedule=slot,
                date=meeting_day,
                defaults={
                    'start_time': slot.start_time,
                    'end_time': slot.end_time,
                    'status': 'S',
                },
            )
            if created:
                created_count += 1
            else:
                existing_count += 1
            meeting_day += timedelta(days=7)

    return {'created': created_count, 'existing': existing_count}
