from django.shortcuts import render, redirect, get_object_or_404
from lms.models import Student, Instructor, Course, CourseCategory, Register, CourseSchedule, CourseTopic, ClassSession, Attendance, Exam, ExamGrade, Certificate, SurveyQuestion, SurveyResponse, SurveyAnswer
from .forms import NewStudentForm, NewInstructorForm, NewCourseForm, NewCourseCategoryForm, NewRegisterForm, CourseScheduleFormSet, CourseTopicFormSet, ExamForm, CertificateForm, SurveyQuestionForm
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.db import transaction, IntegrityError
from django.urls import reverse
from django.db.models import Count, Q, Avg
from django.core.paginator import Paginator
from django.utils import timezone
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError
from decimal import Decimal, InvalidOperation
from django.db.models.deletion import ProtectedError
from .services.session_generator import generate_course_sessions
import csv
from io import BytesIO
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import os
from PIL import Image, ImageDraw, ImageFont, ImageOps, features
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from accounts.views import role_required, is_manager, is_instructor
from django.core.exceptions import PermissionDenied



#region Home Page ( Dashboard )

def _instructor_for(request):
    if is_manager(request.user):
        return None
    return get_object_or_404(Instructor, user=request.user)


def _visible_courses(request):
    if is_manager(request.user):
        return Course.objects.all()
    return Course.objects.filter(schedules__instructor=_instructor_for(request)).distinct()


def _visible_registers(request):
    if is_manager(request.user):
        return Register.objects.all()
    return Register.objects.filter(instructor=_instructor_for(request))


def _visible_students(request):
    if is_manager(request.user):
        return Student.objects.all()
    return Student.objects.filter(register__instructor=_instructor_for(request)).distinct()


def _visible_exams(request):
    if is_manager(request.user):
        return Exam.objects.all()
    return Exam.objects.filter(course__schedules__instructor=_instructor_for(request)).distinct()

@role_required('manager', 'instructor')
def home(request):
    students = _visible_students(request)
    instructors = Instructor.objects.all() if is_manager(request.user) else Instructor.objects.filter(pk=_instructor_for(request).pk)
    courses = _course_cards(_visible_courses(request))
    categories = CourseCategory.objects.filter(course__in=[c.pk for c in courses]).distinct() if not is_manager(request.user) else CourseCategory.objects.all()
    registers = _visible_registers(request)

    context = {
        'students': students,
        'instructors': instructors,
        'courses': courses,
        'categories': categories,
        'registers': registers,
        'students_count': students.count(),
        'instructors_count': instructors.count(),
        'courses_count': len(courses),
        'categories_count': categories.count(),
        'registers_count': registers.count(),
        'today': timezone.localdate(),
        'active_courses_count': _visible_courses(request).filter(course_status__in=['A', 'C']).count(),
        'upcoming_sessions_count': ClassSession.objects.filter(course_schedule__instructor=_instructor_for(request), date__gte=timezone.localdate(), status='S').count() if not is_manager(request.user) else ClassSession.objects.filter(date__gte=timezone.localdate(), status='S').count(),
        'exams_count': _visible_exams(request).count(),
        'upcoming_exams': _visible_exams(request).filter(exam_date__gte=timezone.localdate()).select_related('course').order_by('exam_date')[:4],
    }
    return render(request, 'lms/home.html', context)

#endregion


#region Student CRUD

@role_required('manager')
def add_student(request):
    if request.method == 'POST':
        form = NewStudentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('student_list')
    else:
        form = NewStudentForm()
    return render(request, 'lms/student_form.html', {
        'form': form,
        'page_title': 'Add New Student',
    })


@role_required('manager')
def edit_student(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        form = NewStudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            return redirect('student_list')
    else:
        form = NewStudentForm(instance=student)
    return render(request, 'lms/student_form.html', {
        'form': form,
        'page_title': 'Edit Student',
    })


@role_required('manager')
def delete_student(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        try:
            student.delete()
            return redirect('student_list')
        except ProtectedError:
            return render(request, 'lms/confirm_delete.html', {
                'object': student,
                'page_title': 'Delete Student',
                'cancel_url': 'student_list',
                'delete_error': 'This item has protected historical records (attendance, exams, grades or certificates) and cannot be deleted.',
            })
    return render(request, 'lms/confirm_delete.html', {
        'object': student,
        'page_title': 'Delete Student',
        'cancel_url': 'student_list',
    })

#endregion


#region Instructor CRUD

@role_required('manager')
def add_instructor(request):
    if request.method == 'POST':
        form = NewInstructorForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('instructor_list')
    else:
        form = NewInstructorForm()
    return render(request, 'lms/instructor_form.html', {
        'form': form,
        'page_title': 'Add New Instructor',
    })


@role_required('manager')
def edit_instructor(request, pk):
    instructor = get_object_or_404(Instructor, pk=pk)
    if request.method == 'POST':
        form = NewInstructorForm(request.POST, request.FILES, instance=instructor)
        if form.is_valid():
            form.save()
            return redirect('instructor_list')
    else:
        form = NewInstructorForm(instance=instructor)
    return render(request, 'lms/instructor_form.html', {
        'form': form,
        'page_title': 'Edit Instructor',
    })

@role_required('manager')
def delete_instructor(request, pk):
    instructor = get_object_or_404(Instructor, pk=pk)
    if request.method == 'POST':
        try:
            instructor.delete()
            return redirect('instructor_list')
        except ProtectedError:
            return render(request, 'lms/confirm_delete.html', {
                'object': instructor,
                'page_title': 'Delete Instructor',
                'cancel_url': 'instructor_list',
                'delete_error': 'This item has protected historical records (attendance, exams, grades or certificates) and cannot be deleted.',
            })
    return render(request, 'lms/confirm_delete.html', {
        'object': instructor,
        'page_title': 'Delete Instructor',
        'cancel_url': 'instructor_list',
    })

#endregion


#region Course CRUD

@role_required('manager')
def _course_editor(request, course, page_title):
    """Persist course, weekly slots and ordered syllabus atomically."""
    new_course = not bool(course.pk)
    if request.method == 'POST':
        form = NewCourseForm(request.POST, request.FILES, instance=course)
        schedule_formset = CourseScheduleFormSet(request.POST, instance=course, prefix='schedules')
        topic_formset = CourseTopicFormSet(request.POST, instance=course, prefix='topics')
        if form.is_valid():
            with transaction.atomic():
                saved_course = form.save()
                schedule_formset.require_start_weekday = new_course
                schedules_valid = schedule_formset.is_valid()
                topics_valid = topic_formset.is_valid()
                if schedules_valid and topics_valid:
                    schedule_formset.save()
                    # Save/delete syllabus entries and keep their displayed order.
                    topic_formset.save(commit=False)
                    for deleted_topic in topic_formset.deleted_objects:
                        deleted_topic.delete()
                    topic_position = 0
                    for topic_form in topic_formset.forms:
                        data = getattr(topic_form, 'cleaned_data', {})
                        if not data or data.get('DELETE') or not data.get('title'):
                            continue
                        topic_position += 1
                        topic = topic_form.instance
                        topic.course = saved_course
                        topic.position = topic_position
                        topic.save()
                    generate_course_sessions(saved_course)
                    return redirect(f"{reverse('academic_calendar')}?course={saved_course.pk}")
                transaction.set_rollback(True)
    else:
        form = NewCourseForm(instance=course)
        schedule_formset = CourseScheduleFormSet(instance=course, prefix='schedules')
        topic_formset = CourseTopicFormSet(instance=course, prefix='topics')

    return render(request, 'lms/course_form.html', {
        'form': form,
        'schedule_formset': schedule_formset,
        'topic_formset': topic_formset,
        'page_title': page_title,
    })


@role_required('manager')
def add_course(request):
    return _course_editor(request, Course(), 'Add New Course')


@role_required('manager')
def edit_course(request, pk):
    course = get_object_or_404(Course, pk=pk)
    return _course_editor(request, course, 'Edit Course')

@role_required('manager')
def delete_course(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        try:
            course.delete()
            return redirect('course_list')
        except ProtectedError:
            return render(request, 'lms/confirm_delete.html', {
                'object': course,
                'page_title': 'Delete Course',
                'cancel_url': 'course_list',
                'delete_error': 'This item has protected historical records (attendance, exams, grades or certificates) and cannot be deleted.',
            })
    return render(request, 'lms/confirm_delete.html', {
        'object': course,
        'page_title': 'Delete Course',
        'cancel_url': 'course_list',
    })

#endregion


#region CourseCategory CRUD

@role_required('manager')
def add_course_category(request):
    if request.method == 'POST':
        form = NewCourseCategoryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('category_list')
    else:
        form = NewCourseCategoryForm()
    return render(request, 'lms/course_category_form.html', {
        'form': form,
        'page_title': 'Add New Course Category',
    })

@role_required('manager')
def edit_course_category(request, pk):
    course_category = get_object_or_404(CourseCategory, pk=pk)
    if request.method == 'POST':
        form = NewCourseCategoryForm(request.POST, request.FILES, instance=course_category)
        if form.is_valid():
            form.save()
            return redirect('category_list')
    else:
        form = NewCourseCategoryForm(instance=course_category)
    return render(request, 'lms/course_category_form.html', {
        'form': form,
        'page_title': 'Edit Course Category',
    })

@role_required('manager')
def delete_course_category(request, pk):
    course_category = get_object_or_404(CourseCategory, pk=pk)
    if request.method == 'POST':
        try:
            course_category.delete()
            return redirect('category_list')
        except ProtectedError:
            return render(request, 'lms/confirm_delete.html', {
                'object': course_category,
                'page_title': 'Delete Course Category',
                'cancel_url': 'category_list',
                'delete_error': 'This item has protected historical records (attendance, exams, grades or certificates) and cannot be deleted.',
            })
    return render(request, 'lms/confirm_delete.html', {
        'object': course_category,
        'page_title': 'Delete Course Category',
        'cancel_url': 'category_list',
    })

#endregion


#region Register CRUD

@role_required('manager')
def add_register(request):

    if request.method == 'POST':

        form = NewRegisterForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('register_list')

    else:
        form = NewRegisterForm()

    return render(request, 'lms/register_form.html', {
        'form': form,
        'page_title': 'Register Student',
    })


@role_required('manager')
def edit_register(request, pk):

    register = get_object_or_404(Register, pk=pk)

    if request.method == 'POST':

        form = NewRegisterForm(request.POST, instance=register)

        if form.is_valid():
            form.save()
            return redirect('register_list')

    else:
        form = NewRegisterForm(instance=register)

    return render(request, 'lms/register_form.html', {
        'form': form,
        'page_title': 'Edit Register',
    })


@role_required('manager')
def delete_register(request, pk):

    register = get_object_or_404(Register, pk=pk)

    if request.method == 'POST':
        try:
            register.delete()
            return redirect('register_list')
        except ProtectedError:
            return render(request, 'lms/confirm_delete.html', {
                'object': register,
                'page_title': 'Delete Register',
                'cancel_url': 'register_list',
                'delete_error': 'This item has protected historical records (attendance, exams, grades or certificates) and cannot be deleted.',
            })

    return render(request, 'lms/confirm_delete.html', {
        'object': register,
        'page_title': 'Delete Register',
        'cancel_url': 'register_list',
    })


@role_required('manager')
def get_course_instructors(request, course_id):

    course = get_object_or_404(Course, pk=course_id)

    instructors = course.instructors.all()

    data = [
        {
            'id': instructor.id,
            'name': str(instructor)
        }
        for instructor in instructors
    ]

    return JsonResponse(data, safe=False)

#endregion


#region Calender

@role_required('manager', 'instructor')
def academic_calendar(request):
    sessions = ClassSession.objects.filter(course_schedule__course__in=_visible_courses(request))
    if not is_manager(request.user):
        sessions = sessions.filter(course_schedule__instructor=_instructor_for(request))
    sessions = sessions.select_related(
        'course_schedule__course__course_category', 'course_schedule__instructor',).order_by('date', 'start_time', 'pk')

    calendar_data = [
        {
            'id': session.pk,
            'schedule_id': session.course_schedule_id,
            'course_id': session.course_schedule.course_id,
            'course_title': session.course_schedule.course.title,
            'category_id': session.course_schedule.course.course_category_id,
            'category_name': session.course_schedule.course.course_category.name,
            'instructor_id': session.course_schedule.instructor_id,
            'instructor_name': str(session.course_schedule.instructor),
            'classroom': session.course_schedule.classroom,
            'date': session.date.isoformat(),
            'start_time': session.start_time.strftime('%H:%M'),
            'end_time': session.end_time.strftime('%H:%M'),
            'status': session.status,
            'status_display': session.get_status_display(),
            'cancellation_reason': session.cancellation_reason,
        }
        for session in sessions
    ]
    schedule_qs = CourseSchedule.objects.filter(course__in=_visible_courses(request))
    return render(request, 'lms/calendar.html', {
        'calendar_data': calendar_data,
        'courses_count': len({item['course_id'] for item in calendar_data}),
        'schedules_count': schedule_qs.count(),
        'instructors_count': len({item['instructor_id'] for item in calendar_data}),
        'categories': CourseCategory.objects.filter(course__in=_visible_courses(request)).distinct().order_by('name'),
        'instructors': Instructor.objects.all().order_by('last_name', 'first_name') if is_manager(request.user) else Instructor.objects.filter(pk=_instructor_for(request).pk),
        'unscheduled_courses': _visible_courses(request).filter(schedules__isnull=True).order_by('start_date', 'title'),
        'attendance_base_url': reverse('attendance_dashboard'),
    })

#endregion


#region Attendance

@role_required('manager', 'instructor')

def attendance_dashboard(request):
    courses = _visible_courses(request).order_by('title', 'pk')
    course_id = request.POST.get('course') if request.method == 'POST' else request.GET.get('course')
    session_id = request.POST.get('session') if request.method == 'POST' else request.GET.get('session')

    course = get_object_or_404(courses, pk=course_id) if course_id else None
    session_choices = ClassSession.objects.none()
    if course:
        session_choices = ClassSession.objects.filter(
            course_schedule__course=course,
        )
        if not is_manager(request.user):
            session_choices = session_choices.filter(course_schedule__instructor=_instructor_for(request))
        session_choices = session_choices.select_related('course_schedule__instructor').order_by('date', 'start_time')

    session = None
    if session_id:
        if course is None:
            return HttpResponseBadRequest('Select a course first.')
        session = get_object_or_404(session_choices, pk=session_id)

    register_rows = []
    if session:
        registers = list(
            _visible_registers(request).filter(course=course).select_related('student').order_by(
                'student__last_name', 'student__first_name', 'pk'
            )
        )
        current = {
            record.register_id: record.status
            for record in Attendance.objects.filter(session=session)
        }
        for register in registers:
            register_rows.append({
                'register': register,
                'status': current.get(register.pk, ''),
                'editable': register.status != 'D',
            })

    error_message = ''
    success_message = ''
    if request.method == 'POST':
        if not session:
            return HttpResponseBadRequest('A valid course and session are required.')
        if session.status == 'X':
            error_message = 'Cancelled sessions cannot have attendance recorded.'
        else:
            valid_values = {'', 'P', 'A'}
            editable_rows = [row for row in register_rows if row['editable']]
            submitted = {}
            for row in editable_rows:
                register_id = row['register'].pk
                value = request.POST.get(f'status_{register_id}')
                if value not in valid_values:
                    error_message = 'Invalid attendance selection. Please retry.'
                    break
                submitted[register_id] = value
            wants_completed = request.POST.get('mark_completed') == 'on'
            if not error_message and wants_completed and (
                not editable_rows or not all(submitted.values())
            ):
                error_message = 'Mark all active registers before completing the session.'
            if not error_message:
                with transaction.atomic():
                    for row in editable_rows:
                        register = row['register']
                        value = submitted[register.pk]
                        if value:
                            Attendance.objects.update_or_create(
                                session=session,
                                register=register,
                                defaults={'status': value},
                            )
                        else:
                            Attendance.objects.filter(session=session, register=register).delete()
                    if wants_completed and session.status != 'C':
                        session.status = 'C'
                        session.full_clean()
                        session.save(update_fields=['status'])
                return redirect(f'{reverse("attendance_dashboard")}?course={course.pk}&session={session.pk}&saved=1')

            for row in register_rows:
                if row['editable']:
                    row['status'] = request.POST.get(f'status_{row["register"].pk}', '')

    if request.GET.get('saved') == '1':
        success_message = 'Attendance saved successfully.'

    return render(request, 'lms/attendance.html', {
        'courses': courses,
        'course': course,
        'session_choices': session_choices,
        'session': session,
        'register_rows': register_rows,
        'present_count': sum(row['status'] == 'P' for row in register_rows),
        'absent_count': sum(row['status'] == 'A' for row in register_rows),
        'unmarked_count': sum(not row['status'] for row in register_rows),
        'error_message': error_message,
        'success_message': success_message,
    })

#endregion


#region CSV

def _safe_csv_cell(value):
    text = str(value if value is not None else '')
    if text.lstrip().startswith(('=', '+', '-', '@')) or text.startswith(('\t', '\r', '\n')):
        return "'" + text
    return text


def _csv_response(filename):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write('\ufeff')  # UTF-8 BOM so Excel handles future Persian names.
    return response


@role_required('manager', 'instructor')
def attendance_session_csv(request, session_id):
    session = get_object_or_404(
        ClassSession.objects.filter(course_schedule__course__in=_visible_courses(request)).select_related('course_schedule__course', 'course_schedule__instructor'),
        pk=session_id,
    )
    if not is_manager(request.user) and session.course_schedule.instructor_id != _instructor_for(request).pk:
        raise PermissionDenied('Another instructor owns this session.')
    response = _csv_response(f'attendance-session-{session.pk}-{session.date.isoformat()}.csv')
    writer = csv.writer(response)
    writer.writerow(['Course', 'Session date', 'Start time', 'End time', 'Instructor',
                     'Session status', 'Student', 'Register ID', 'Register status', 'Attendance'])
    marked = {
        row.register_id: row.get_status_display()
        for row in Attendance.objects.filter(session=session)
    }
    for register in _visible_registers(request).filter(course=session.course_schedule.course).select_related('student').order_by('student__last_name', 'student__first_name'):
        writer.writerow([_safe_csv_cell(session.course_schedule.course.title),
                         session.date.isoformat(), session.start_time.strftime('%H:%M'),
                         session.end_time.strftime('%H:%M'),
                         _safe_csv_cell(str(session.course_schedule.instructor)),
                         session.get_status_display(),
                         _safe_csv_cell(str(register.student)), register.pk,
                         register.get_status_display(), marked.get(register.pk, 'Unmarked')])
    return response


@role_required('manager', 'instructor')
def attendance_course_csv(request, course_id):
    course = get_object_or_404(_visible_courses(request), pk=course_id)
    completed = ClassSession.objects.filter(
        course_schedule__course=course, status='C'
    )
    if not is_manager(request.user):
        completed = completed.filter(course_schedule__instructor=_instructor_for(request))
    completed_count = completed.count()
    results = (
        Attendance.objects.filter(session__in=completed)
        .values('register_id', 'status')
        .annotate(total=Count('id'))
    )
    totals = {}
    for result in results:
        totals.setdefault(result['register_id'], {})[result['status']] = result['total']

    response = _csv_response(f'attendance-course-{course.pk}.csv')
    writer = csv.writer(response)
    writer.writerow(['Course', 'Student', 'Register ID', 'Register status',
                     'Completed sessions', 'Present', 'Absent', 'Unmarked', 'Attendance % (marked only)'])
    for register in _visible_registers(request).filter(course=course).select_related('student').order_by('student__last_name', 'student__first_name'):
        counts = totals.get(register.pk, {})
        present, absent = counts.get('P', 0), counts.get('A', 0)
        marked = present + absent
        percentage = f'{100 * present / marked:.1f}' if marked else ''
        writer.writerow([_safe_csv_cell(course.title), _safe_csv_cell(str(register.student)),
                         register.pk, register.get_status_display(), completed_count,
                         present, absent, max(0, completed_count - marked), percentage])
    return response


@role_required('manager', 'instructor')
def legacy_calendar_redirect(request):
    return redirect('academic_calendar')

#endregion


#region read-only profiles

def _course_cards(queryset):
    courses = list(queryset.select_related('course_category').prefetch_related('instructors').annotate(
        occupied_seats=Count('register', filter=Q(register__status='A'), distinct=True)
    ))
    for course in courses:
        course.capacity_percent = min(100, round(100 * course.occupied_seats / course.capacity)) if course.capacity > 0 else 0
        course.capacity_offset = round(264 * (1 - course.capacity_percent / 100), 2)
        course.available_seats = max(0, course.capacity - course.occupied_seats)
    return courses


@role_required('manager', 'instructor')
def student_list(request):
    query = request.GET.get('q', '').strip()
    students = _visible_students(request).order_by('last_name', 'first_name', 'pk')
    if query:
        students = students.filter(Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(city__icontains=query))
    return render(request, 'lms/student_list.html', {
        'students': Paginator(students, 12).get_page(request.GET.get('page')),
        'q': query, 'total_count': _visible_students(request).count(),
    })


@role_required('manager', 'instructor')
def student_detail(request, pk):
    student = get_object_or_404(_visible_students(request), pk=pk)
    registers = _visible_registers(request).filter(student=student).select_related('course', 'instructor').order_by('-register_date')
    return render(request, 'lms/student_detail.html', {'student': student, 'registers': registers,
        'survey_responses': SurveyResponse.objects.filter(register__student=student).select_related('course').annotate(average_rating=Avg('answers__rating')) if is_manager(request.user) else []})


@role_required('manager', 'instructor')
def instructor_list(request):
    query = request.GET.get('q', '').strip()
    instructors = (Instructor.objects.all() if is_manager(request.user) else Instructor.objects.filter(pk=_instructor_for(request).pk)).order_by('last_name', 'first_name', 'pk')
    if query:
        instructors = instructors.filter(Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(city__icontains=query))
    return render(request, 'lms/instructor_list.html', {
        'instructors': Paginator(instructors, 12).get_page(request.GET.get('page')),
        'q': query, 'total_count': instructors.count(),
    })


@role_required('manager', 'instructor')
def instructor_detail(request, pk):
    instructor = get_object_or_404(Instructor.objects.all() if is_manager(request.user) else Instructor.objects.filter(user=request.user), pk=pk)
    return render(request, 'lms/instructor_detail.html', {
        'instructor': instructor,
        'courses': _course_cards(instructor.course_set.all()),
        'schedules': CourseSchedule.objects.filter(instructor=instructor).select_related('course').order_by('weekday', 'start_time'),
        'survey_responses': SurveyResponse.objects.filter(instructor=instructor).select_related('course').annotate(average_rating=Avg('answers__rating')),
    })


@role_required('manager', 'instructor')
def course_list(request):
    query = request.GET.get('q', '').strip()
    courses = _visible_courses(request).order_by('title', 'pk')
    if query:
        courses = courses.filter(Q(title__icontains=query) | Q(course_category__name__icontains=query))
    category_id = request.GET.get('category', '')
    if category_id.isdecimal():
        courses = courses.filter(course_category_id=int(category_id))
    all_courses = _course_cards(courses)
    return render(request, 'lms/course_list.html', {
        'courses': Paginator(all_courses, 9).get_page(request.GET.get('page')),
        'q': query, 'category_id': category_id, 'categories': CourseCategory.objects.order_by('name'),
        'total_count': _visible_courses(request).count(),
    })


@role_required('manager', 'instructor')
def course_detail(request, pk):
    course = get_object_or_404(_visible_courses(request), pk=pk)
    course = _course_cards(Course.objects.filter(pk=course.pk))[0]
    return render(request, 'lms/course_detail.html', {
        'course': course,
        'schedules': course.schedules.select_related('instructor').filter(instructor=_instructor_for(request)).order_by('weekday', 'start_time') if not is_manager(request.user) else course.schedules.select_related('instructor').order_by('weekday', 'start_time'),
        'registers': _visible_registers(request).filter(course=course).select_related('student').order_by('student__last_name', 'student__first_name'),
        'exams': course.exams.all()[:6],
        'topics': course.topics.all(),
    })


@role_required('manager', 'instructor')
def category_list(request):
    visible_courses = _visible_courses(request)

    if is_manager(request.user):
        categories = CourseCategory.objects.all()
    else:
        categories = CourseCategory.objects.filter(
            course__in=visible_courses
        ).distinct()

    categories = categories.annotate(
        course_count=Count(
            'course',
            filter=Q(course__in=visible_courses),
            distinct=True
        )
    ).order_by('name')

    return render(request, 'lms/category_list.html', {
        'categories': categories
    })


@role_required('manager', 'instructor')
def category_detail(request, pk):
    category = get_object_or_404(CourseCategory, pk=pk)
    if not _visible_courses(request).filter(course_category=category).exists():
        raise PermissionDenied('No related courses.')
    return render(request, 'lms/category_detail.html', {
        'category': category, 'courses': _course_cards(_visible_courses(request).filter(course_category=category).order_by('title')),
    })


@role_required('manager', 'instructor')
def register_list(request):
    registers = _visible_registers(request).select_related('student', 'course', 'instructor').order_by('-register_date', '-pk')
    query = request.GET.get('q', '').strip()
    if query:
        registers = registers.filter(Q(student__first_name__icontains=query) | Q(student__last_name__icontains=query) | Q(course__title__icontains=query))
    return render(request, 'lms/register_list.html', {
        'registers': Paginator(registers, 20).get_page(request.GET.get('page')),
        'q': query,
    })

#endregion


#region Exam CRUD

@role_required('manager', 'instructor')
def exam_list(request):
    query = request.GET.get('q', '').strip()
    exam_type = request.GET.get('type', '')
    exams = _visible_exams(request).select_related('course').annotate(graded_count=Count('grades')).order_by('-exam_date', '-pk')
    if query:
        exams = exams.filter(Q(title__icontains=query) | Q(course__title__icontains=query))
    if exam_type in ('O', 'F'):
        exams = exams.filter(exam_type=exam_type)
    return render(request, 'lms/exam_list.html', {
        'exams': Paginator(exams, 12).get_page(request.GET.get('page')),
        'q': query, 'exam_type': exam_type,
        'exam_count': _visible_exams(request).count(),
        'upcoming_count': _visible_exams(request).filter(exam_date__gte=timezone.localdate()).count(),
    })


@role_required('manager')
def _exam_editor(request, exam, title):
    form = ExamForm(request.POST or None, instance=exam)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('exam_list')
    return render(request, 'lms/exam_form.html', {'form': form, 'page_title': title})


@role_required('manager')
def add_exam(request):
    return _exam_editor(request, None, 'Add Exam')


@role_required('manager')
def edit_exam(request, pk):
    return _exam_editor(request, get_object_or_404(Exam, pk=pk), 'Edit Exam')


@role_required('manager', 'instructor')
def exam_detail(request, pk):
    exam = get_object_or_404(_visible_exams(request).select_related('course'), pk=pk)
    grades = exam.grades.select_related('register__student').filter(register__in=_visible_registers(request)).order_by('register__student__last_name')
    return render(request, 'lms/exam_detail.html', {'exam': exam, 'grades': grades})


@role_required('manager')
def delete_exam(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    if request.method == 'POST':
        exam.delete()
        return redirect('exam_list')
    return render(request, 'lms/confirm_delete.html', {
        'object': exam, 'page_title': 'Delete Exam', 'cancel_url': 'exam_list',
        'delete_note': 'All grades for this exam will also be deleted.',
    })


@role_required('manager', 'instructor')
def exam_grades(request, pk):
    exam = get_object_or_404(_visible_exams(request).select_related('course'), pk=pk)
    registers = list(_visible_registers(request).filter(course=exam.course).select_related('student').order_by(
        'student__last_name', 'student__first_name', 'pk'))
    existing = {grade.register_id: grade for grade in ExamGrade.objects.filter(exam=exam, register__in=registers)}
    errors, success = {}, request.GET.get('saved') == '1'
    submitted = {}
    if request.method == 'POST':
        for reg in registers:
            if reg.status == 'D':
                continue
            data = {}
            for key in ('score', 'written_score', 'practical_score'):
                field = f'{key}_{reg.pk}' if key != 'score' else f'grade_{reg.pk}'
                raw = request.POST.get(field, '').strip()
                if not raw:
                    data[key] = None
                    continue
                try:
                    number = Decimal(raw)
                    if not number.is_finite() or number.as_tuple().exponent < -2 or not (0 <= number <= exam.max_score):
                        raise ValueError
                    data[key] = number
                except (ValueError, InvalidOperation):
                    errors[reg.pk] = f'Enter values from 0 to {exam.max_score} (up to 2 decimals).'


            if data['score'] is None and (data['written_score'] is not None or data['practical_score'] is not None):
                errors[reg.pk] = 'Enter a final grade when recording written or practical marks.'
            submitted[reg.pk] = data
        if not errors:
            with transaction.atomic():
                for reg in registers:
                    if reg.status == 'D':
                        continue
                    data = submitted[reg.pk]
                    if data['score'] is None:
                        ExamGrade.objects.filter(exam=exam, register=reg).delete()
                    else:
                        ExamGrade.objects.update_or_create(exam=exam, register=reg, defaults=data)
            return redirect(f'{reverse("exam_grades", args=[exam.pk])}?saved=1')

    rows = []
    for reg in registers:
        old = existing.get(reg.pk)
        data = {
            'score': old.score if old else None,
            'written_score': old.written_score if old else None,
            'practical_score': old.practical_score if old else None,
        }
        if request.method == 'POST' and reg.status != 'D':
            for key in data:
                field = f'{key}_{reg.pk}' if key != 'score' else f'grade_{reg.pk}'
                data[key] = request.POST.get(field, '').strip()
        rows.append({'register': reg, **data, 'error': errors.get(reg.pk, ''),
                     'passed': old.passed if old else False})
    return render(request, 'lms/exam_grades.html', {
        'exam': exam, 'rows': rows, 'errors': errors, 'success': success,
        'graded_count': len(existing),
    })


@role_required('manager', 'instructor')
def exam_grades_csv(request, pk):
    exam = get_object_or_404(_visible_exams(request).select_related('course'), pk=pk)
    grades = {grade.register_id: grade for grade in exam.grades.filter(register__in=_visible_registers(request))}
    response = _csv_response(f'exam-{exam.pk}-grades.csv')
    writer = csv.writer(response)
    writer.writerow(['Exam', 'Course', 'Type', 'Exam Date', 'Student', 'Register ID',
                     'Register Status', 'Final Score', 'Written Score', 'Practical Score',
                     'Max Score', 'Passing Score', 'Result'])
    for reg in _visible_registers(request).filter(course=exam.course).select_related('student').order_by('student__last_name', 'student__first_name'):
        grade = grades.get(reg.pk)
        result = ('Passed' if grade.passed else 'Failed') if grade else 'Not graded'
        writer.writerow([_safe_csv_cell(exam.title), _safe_csv_cell(exam.course.title),
                         exam.get_exam_type_display(), exam.exam_date.isoformat(),
                         _safe_csv_cell(str(reg.student)), reg.pk, reg.get_status_display(),
                         str(grade.score) if grade else '',
                         str(grade.written_score) if grade and grade.written_score is not None else '',
                         str(grade.practical_score) if grade and grade.practical_score is not None else '',
                         str(exam.max_score), str(exam.passing_score), result])
    return response

#endregion


#region CSV Reports

REPORT_SECTIONS = frozenset({
    'overview', 'students', 'instructors', 'courses', 'categories', 'registers',
    'schedules', 'sessions', 'attendance', 'exams', 'grades', 'certificates',
    'surveys', 'questions', 'topics', 'users',
})
MANAGER_ONLY_REPORTS = frozenset({'certificates', 'questions', 'users'})


@role_required('manager', 'instructor')
def report_csv(request, section):

    if section not in REPORT_SECTIONS:
        from django.http import Http404
        raise Http404('Unknown report type')
    if section in MANAGER_ONLY_REPORTS and not is_manager(request.user):
        raise PermissionDenied('This report requires Manager access.')
    q = request.GET.get('q', '').strip()[:150]
    category = request.GET.get('category', '').strip()
    course_id = request.GET.get('course', '').strip()
    exam_id = request.GET.get('exam', '').strip()
    response = _csv_response(f'sematec-{section}-{timezone.localdate().isoformat()}.csv')
    writer = csv.writer(response)

    def emit(*values):
        writer.writerow([value if isinstance(value, (int, float, Decimal)) else
                         _safe_csv_cell(value) for value in values])

    def in_course(queryset, field='course'):
        if course_id:
            if not course_id.isdecimal():
                from django.http import Http404
                raise Http404('Invalid course')
            queryset = queryset.filter(**{f'{field}_id': int(course_id)})
        return queryset

    def filtered_courses():
        queryset = _visible_courses(request).select_related('course_category').prefetch_related('instructors')
        if q:
            queryset = queryset.filter(Q(title__icontains=q) | Q(course_category__name__icontains=q))
        if category.isdecimal():
            queryset = queryset.filter(course_category_id=int(category))
        if course_id.isdecimal():
            queryset = queryset.filter(pk=int(course_id))
        return queryset.distinct().order_by('title', 'pk')

    if section == 'overview':
        emit('Metric', 'Value')
        emit('Report date', timezone.localdate().isoformat())
        emit('Students', _visible_students(request).count())
        emit('Instructors', Instructor.objects.count() if is_manager(request.user) else 1)
        emit('Courses', _visible_courses(request).count())
        emit('Registers', _visible_registers(request).count())
        emit('Exams', _visible_exams(request).count())
        emit('Upcoming sessions', ClassSession.objects.filter(
            course_schedule__course__in=_visible_courses(request),
            date__gte=timezone.localdate(), status='S',
            **({} if is_manager(request.user) else {'course_schedule__instructor': _instructor_for(request)}),
        ).count())

    elif section == 'students':
        emit('ID', 'First name', 'Last name', 'National code', 'Birth date', 'Gender',
             'Education', 'Job title', 'Organizational position', 'Workplace',
             'Phone', 'Email', 'City', 'Address')
        queryset = _visible_students(request).order_by('last_name', 'first_name', 'pk')
        student_id = request.GET.get('student', '')
        if student_id.isdecimal():
            queryset = queryset.filter(pk=int(student_id))
        if q:
            queryset = queryset.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(city__icontains=q))
        for student in queryset:
            emit(student.pk, student.first_name, student.last_name, student.national_code,
                 student.birth_date.isoformat(), student.get_gender_display(),
                 student.get_educational_certification_display(), student.job_title,
                 student.get_organizational_position_display(), student.work_place,
                 student.phone_number,
                 student.email, student.city, student.address)

    elif section == 'instructors':
        emit('ID', 'First name', 'Last name', 'National code', 'Education',
             'Phone', 'Email', 'City', 'Linked account')
        queryset = Instructor.objects.all() if is_manager(request.user) else Instructor.objects.filter(pk=_instructor_for(request).pk)
        instructor_id = request.GET.get('instructor', '')
        if instructor_id.isdecimal():
            queryset = queryset.filter(pk=int(instructor_id))
        if q:
            queryset = queryset.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(city__icontains=q))
        for instructor in queryset.select_related('user').order_by('last_name', 'first_name', 'pk'):
            emit(instructor.pk, instructor.first_name, instructor.last_name, instructor.national_code,
                 instructor.get_educational_certification_display(), instructor.phone_number,
                 instructor.email, instructor.city, instructor.user.username if instructor.user_id else '')

    elif section == 'courses':
        emit('ID', 'Course', 'Category', 'Instructors', 'Status', 'Level', 'Delivery mode', 'Start date',
             'End date', 'Duration (hours)', 'Capacity', 'Active registers', 'Available seats',
             'Price (toman)', 'Description')
        for course in filtered_courses():
            active = _visible_registers(request).filter(course=course, status='A').count()
            emit(course.pk, course.title, course.course_category.name,
                 ', '.join(str(p) for p in course.instructors.all()), course.get_course_status_display(),
                 course.get_course_level_display(), course.get_delivery_mode_display(), course.start_date.isoformat(), course.end_date.isoformat(),
                 course.duration, course.capacity, active, max(0, course.capacity-active),
                 course.price, course.description)

    elif section == 'categories':
        emit('ID', 'Category', 'Visible courses')
        queryset = CourseCategory.objects.filter(course__in=_visible_courses(request)).distinct() if not is_manager(request.user) else CourseCategory.objects.all()
        for item in queryset.order_by('name'):
            emit(item.pk, item.name, _visible_courses(request).filter(course_category=item).count())

    elif section == 'registers':
        emit('ID', 'Student', 'Student national code', 'Course', 'Instructor', 'Registered',
             'Status', 'Completed on')
        queryset = _visible_registers(request).select_related('student', 'course', 'instructor')
        queryset = in_course(queryset)
        if q:
            queryset = queryset.filter(Q(student__first_name__icontains=q) | Q(student__last_name__icontains=q) |
                                       Q(course__title__icontains=q))
        for item in queryset.order_by('-register_date', '-pk'):
            emit(item.pk, str(item.student), item.student.national_code, item.course.title,
                 str(item.instructor), item.register_date.isoformat(), item.get_status_display(),
                 item.completed_on.isoformat() if item.completed_on else '')

    elif section == 'schedules':
        emit('ID', 'Course', 'Instructor', 'Day', 'Room', 'Start time', 'End time', 'Course status')
        queryset = CourseSchedule.objects.filter(course__in=_visible_courses(request))
        if not is_manager(request.user):
            queryset = queryset.filter(instructor=_instructor_for(request))
        for item in in_course(queryset).select_related('course', 'instructor').order_by('course__title', 'weekday', 'start_time'):
            emit(item.pk, item.course.title, str(item.instructor), item.get_weekday_display(), item.classroom,
                 item.start_time.strftime('%H:%M'), item.end_time.strftime('%H:%M'), item.course.get_course_status_display())

    elif section == 'sessions':
        emit('ID', 'Course', 'Date', 'Start time', 'End time', 'Instructor', 'Room', 'Status', 'Cancellation reason')
        queryset = ClassSession.objects.filter(course_schedule__course__in=_visible_courses(request))
        if not is_manager(request.user):
            queryset = queryset.filter(course_schedule__instructor=_instructor_for(request))
        if course_id:
            queryset = in_course(queryset, 'course_schedule__course')
        for item in queryset.select_related('course_schedule__course', 'course_schedule__instructor').order_by('date', 'start_time'):
            slot = item.course_schedule
            emit(item.pk, slot.course.title, item.date.isoformat(), item.start_time.strftime('%H:%M'),
                 item.end_time.strftime('%H:%M'), str(slot.instructor), slot.classroom,
                 item.get_status_display(), item.cancellation_reason)

    elif section == 'attendance':
        emit('Session ID', 'Course', 'Date', 'Room', 'Instructor', 'Student', 'Register ID',
             'Register status', 'Presence', 'Recorded at')
        queryset = Attendance.objects.filter(session__course_schedule__course__in=_visible_courses(request),
                                              register__in=_visible_registers(request))
        if not is_manager(request.user):
            queryset = queryset.filter(session__course_schedule__instructor=_instructor_for(request))
        if course_id:
            queryset = in_course(queryset, 'session__course_schedule__course')
        for item in queryset.select_related('session__course_schedule__course', 'session__course_schedule__instructor',
                                            'register__student', 'register__course').order_by('session__date', 'register__student__last_name'):
            slot = item.session.course_schedule
            emit(item.session_id, slot.course.title, item.session.date.isoformat(), slot.classroom,
                 str(slot.instructor), str(item.register.student), item.register_id,
                 item.register.get_status_display(), item.get_status_display(), item.recorded_at.isoformat())

    elif section == 'exams':
        emit('ID', 'Title', 'Course', 'Type', 'Date', 'Status (by date)', 'Maximum score', 'Passing score', 'Grades recorded', 'Description')
        queryset = _visible_exams(request).select_related('course').annotate(graded_count=Count('grades'))
        if q:
            queryset = queryset.filter(Q(title__icontains=q) | Q(course__title__icontains=q))
        if request.GET.get('type') in ('O', 'F'):
            queryset = queryset.filter(exam_type=request.GET['type'])
        if course_id:
            queryset = in_course(queryset)
        for item in queryset.order_by('-exam_date', '-pk'):
            emit(item.pk, item.title, item.course.title, item.get_exam_type_display(), item.exam_date.isoformat(),
                 'Upcoming' if item.exam_date >= timezone.localdate() else 'Past', item.max_score,
                 item.passing_score, item.graded_count, item.description)

    elif section == 'grades':
        emit('Exam ID', 'Exam', 'Course', 'Student', 'Register ID', 'Final score',
             'Written score', 'Practical score', 'Maximum score', 'Passing score', 'Result')
        queryset = ExamGrade.objects.filter(exam__in=_visible_exams(request), register__in=_visible_registers(request))
        if course_id:
            queryset = in_course(queryset, 'exam__course')
        if exam_id:
            if not exam_id.isdecimal():
                from django.http import Http404
                raise Http404('Invalid exam')
            queryset = queryset.filter(exam_id=int(exam_id))
        for item in queryset.select_related('exam__course', 'register__student').order_by('exam__exam_date', 'register__student__last_name'):
            emit(item.exam_id, item.exam.title, item.exam.course.title, str(item.register.student), item.register_id,
                 item.score, item.written_score if item.written_score is not None else '',
                 item.practical_score if item.practical_score is not None else '',
                 item.exam.max_score, item.exam.passing_score, 'Passed' if item.passed else 'Failed')

    elif section == 'certificates':
        emit('Serial number', 'Student', 'Course', 'Grade', 'Issue date', 'Course hours',
             'Persian student name', 'Persian course title', 'Created at')
        queryset = Certificate.objects.select_related('register__student', 'register__course')
        if q:
            queryset = queryset.filter(Q(serial_number__icontains=q) | Q(student_name__icontains=q) |
                                       Q(course_title__icontains=q))
        if course_id:
            queryset = in_course(queryset, 'register__course')
        for item in queryset.order_by('-issue_date', '-pk'):
            emit(item.serial_number, item.student_name, item.course_title, item.grade,
                 item.issue_date.isoformat(), item.course_hours, item.student_name_fa,
                 item.course_title_fa, item.created_at.isoformat())

    elif section == 'surveys':
        emit('Response ID', 'Course', 'Audience', 'Respondent', 'Question', 'Rating', 'Recorded by', 'Updated at')
        queryset = SurveyAnswer.objects.filter(response__course__in=_visible_courses(request))
        if not is_manager(request.user):
            queryset = queryset.filter(response__audience='I', response__instructor=_instructor_for(request))
        if course_id:
            queryset = in_course(queryset, 'response__course')
        for item in queryset.select_related('response__course', 'response__instructor',
                                            'response__register__student', 'response__recorded_by', 'question').order_by('response__course__title', 'response_id', 'question__position'):
            respondent = item.response.instructor or (item.response.register.student if item.response.register else '')
            emit(item.response_id, item.response.course.title, item.response.get_audience_display(),
                 str(respondent), item.question.title, item.rating,
                 item.response.recorded_by.username if item.response.recorded_by else '',
                 item.response.updated_at.isoformat())

    elif section == 'questions':
        emit('ID', 'Audience', 'Question', 'Position', 'Active', 'Archived')
        for item in SurveyQuestion.objects.order_by('audience', 'position', 'pk'):
            emit(item.pk, item.get_audience_display(), item.title, item.position,
                 'Yes' if item.active else 'No', 'Yes' if item.archived else 'No')

    elif section == 'users':
        from django.contrib.auth import get_user_model
        emit('ID', 'Username', 'First name', 'Last name', 'Email', 'Role', 'Instructor profile', 'Active')
        for user in get_user_model().objects.prefetch_related('groups').select_related('instructor_profile').order_by('username'):
            linked = getattr(user, 'instructor_profile', None)
            roles = ', '.join(group.name for group in user.groups.all())
            emit(user.pk, user.username, user.first_name, user.last_name, user.email,
                 'Manager' if user.is_superuser else roles, str(linked) if linked else '',
                 'Yes' if user.is_active else 'No')

    elif section == 'topics':
        emit('ID', 'Course', 'Position', 'Topic')
        queryset = CourseTopic.objects.filter(course__in=_visible_courses(request))
        for item in in_course(queryset).select_related('course').order_by('course__title', 'position'):
            emit(item.pk, item.course.title, item.position, item.title)

    return response

#endregion


#region Certification

WIDTH, HEIGHT = 2480, 1754  # Landscape A4 aspect ratio at ~212 DPI.
NAVY = '#172d55'
BLUE = '#203d73'
GOLD = '#be9853'
LIGHT_GOLD = '#e6d9b7'
CREAM = '#fcfaf5'
MUTED = '#6a7487'


@dataclass(frozen=True)
class CertificateContent:
    student_name: str
    course_title: str
    duration: int
    grade: str
    serial_number: str
    issue_date: date
    student_name_fa: str = ''
    course_title_fa: str = ''


def _font_paths(kind):
    win = Path(os.environ.get('WINDIR', r'C:\Windows')) / 'Fonts'
    if kind == 'persian':
        return [
            win / 'tahoma.ttf', win / 'arial.ttf',
            Path('/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf'),
            Path('/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf'),
            Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
        ]
    if kind == 'persian_bold':
        return [
            win / 'tahomabd.ttf', win / 'arialbd.ttf', win / 'tahoma.ttf',
            Path('/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf'),
            Path('/usr/share/fonts/truetype/noto/NotoNaskhArabic-Bold.ttf'),
            Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
        ]
    if kind == 'display':
        return [
            win / 'georgiab.ttf', win / 'timesbd.ttf',
            Path('/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf'),
            Path('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'),
        ]
    return [
        win / 'arial.ttf', win / 'segoeui.ttf',
        Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
    ]


def _font(kind, size):
    for path in _font_paths(kind):
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    raise RuntimeError(
        f'No usable {kind} font found. Install an Arabic-capable system font '
        '(for example, Tahoma on Windows) and restart the server.'
    )


def _contains_persian(text):
    return any('\u0600' <= char <= '\u06ff' for char in str(text))


def _farsi_digits(value):
    return str(value).translate(str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹'))


def _prepare_text(text, *, persian, has_raqm):

    if not persian:
        return text, {}  # Passing direction='ltr' also fails without RAQM.
    if has_raqm:
        return text, {'direction': 'rtl'}
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
    except ImportError as exc:
        raise RuntimeError(
            'Persian certificate needs arabic-reshaper and python-bidi when '
            'Pillow has no RAQM. Run: pip install -r requirements.txt'
        ) from exc
    return get_display(arabic_reshaper.reshape(text)), {}


def _fit(draw, value, center_x, center_y, max_width, size, *, kind='body', fill=NAVY,
         min_size=38, language='en', max_height=None):
    text = str(value or '').strip() or '—'
    is_persian = _contains_persian(text)
    chosen_kind = ('persian_bold' if kind == 'display' else 'persian') if is_persian else kind
    has_raqm = features.check('raqm')
    # The same text shaping path is used for measuring, wrapping and painting.
    def prepare(line):
        return _prepare_text(line, persian=_contains_persian(line), has_raqm=has_raqm)

    def fits(line, font):
        prepared, options = prepare(line)
        return draw.textlength(prepared, font=font, **options) <= max_width

    font = _font(chosen_kind, size)
    while not fits(text, font) and size > min_size:
        size = max(min_size, size - 2)
        font = _font(chosen_kind, size)

    if not fits(text, font):
        words = text.split()
        first, second = [], []
        for word in words:
            candidate = ' '.join(first + [word])
            if not first or fits(candidate, font):
                first.append(word)
            else:
                second.append(word)
        if second and fits(' '.join(first), font) and fits(' '.join(second), font):
            offset = min(39, size // 2)
            for line, y in [(' '.join(first), center_y - offset), (' '.join(second), center_y + offset)]:
                glyphs, options = prepare(line)
                draw.text((center_x, y), glyphs, font=font, fill=fill, anchor='mm', **options)
            return
        while len(text) > 3 and not fits(text + '…', font):
            text = text[:-1]
        text += '…'
    glyphs, options = prepare(text)
    draw.text((center_x, center_y), glyphs, font=font, fill=fill, anchor='mm', **options)


def build_certificate_image(content, *, language='en', logo_path=None):
    if language not in ('en', 'fa'):
        raise ValueError('Unsupported certificate language.')

    image = Image.new('RGB', (WIDTH, HEIGHT), CREAM)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((82, 78, WIDTH-82, HEIGHT-78), radius=27, outline=GOLD, width=8)
    draw.rounded_rectangle((110, 106, WIDTH-110, HEIGHT-106), radius=19, outline=LIGHT_GOLD, width=3)
    draw.line((210, 140, 640, 140), fill=GOLD, width=5)
    draw.line((WIDTH-640, 140, WIDTH-210, 140), fill=GOLD, width=5)
    draw.line((210, HEIGHT-143, 640, HEIGHT-143), fill=GOLD, width=5)
    draw.line((WIDTH-640, HEIGHT-143, WIDTH-210, HEIGHT-143), fill=GOLD, width=5)
    for x, y in [(165,165),(WIDTH-165,165),(165,HEIGHT-165),(WIDTH-165,HEIGHT-165)]:
        draw.ellipse((x-13,y-13,x+13,y+13),fill=GOLD)
    draw.arc((-350, 1190, 700, 2250), 260, 345, fill='#e9e4d9', width=6)
    draw.arc((WIDTH-700, 1190, WIDTH+350, 2250), 195, 280, fill='#e9e4d9', width=6)

    logo = Path(logo_path) if logo_path else Path(__file__).resolve().parent / 'static/lms/images/logo.jpg'
    if logo.is_file():
        with Image.open(logo) as source:
            source = ImageOps.fit(source.convert('RGB'), (230,230), method=Image.Resampling.LANCZOS)
            mask = Image.new('L', (230,230), 0)
            ImageDraw.Draw(mask).ellipse((0,0,229,229), fill=255)
            image.paste(source, (WIDTH//2-115, 173), mask)
    else:
        _fit(draw, 'SEMATEC', WIDTH//2, 270, 900, 80, kind='display')

    _fit(draw, 'SEMATEC · IT TRAINING CENTER', WIDTH//2, 454, 1500, 34, fill=MUTED)
    draw.line((850, 496, 1630, 496), fill=LIGHT_GOLD, width=4)

    if language == 'fa':
        title = 'گواهینامه آموزشی'
        kicker = 'این گواهینامه به'
        student = content.student_name_fa or content.student_name
        message = 'به پاس شرکت در دوره آموزشی و ارزیابی اعطا می‌شود'
        course = content.course_title_fa or content.course_title
        duration = f'مدت دوره: {_farsi_digits(content.duration)} ساعت'
        cards = [
            ('نمره از ۱۰۰', _farsi_digits(content.grade)),
            ('تاریخ صدور میلادی', _farsi_digits(content.issue_date.isoformat())),
            ('شماره سریال', content.serial_number),
        ]
        footer = 'صادرشده توسط مرکز آموزش فناوری اطلاعات سماتک'
    else:
        title = 'CERTIFICATE OF TRAINING'
        kicker = 'PROUDLY PRESENTED TO'
        student = content.student_name
        message = 'In recognition of participation and assessment in the course'
        course = content.course_title
        duration = f'TRAINING DURATION  ·  {content.duration} HOURS'
        cards = [('GRADE / 100', content.grade), ('DATE OF ISSUE', content.issue_date.isoformat()),
                 ('CERTIFICATE SERIAL', content.serial_number)]
        footer = 'Issued by Sematec IT Training Center  •  Official training record'

    _fit(draw, title, WIDTH//2, 584, 2030, 87, kind='display', fill=BLUE, language=language)
    _fit(draw, kicker, WIDTH//2, 712, 1700, 38, fill=MUTED, language=language)
    _fit(draw, student, WIDTH//2, 855, 2000, 112, kind='display', min_size=49, fill=NAVY, language=language)
    draw.line((795, 929, 1685, 929), fill=GOLD, width=4)
    _fit(draw, message, WIDTH//2, 1001, 1980, 42, fill=MUTED, language=language)
    _fit(draw, course, WIDTH//2, 1137, 2020, 78, kind='display', min_size=43, fill=BLUE, language=language)
    _fit(draw, duration, WIDTH//2, 1245, 1740, 38, fill=MUTED, language=language)

    for i, (label, value) in enumerate(cards):
        left = 220 + i * 688
        right = left + 666
        draw.rounded_rectangle((left, 1335, right, 1517), radius=14,
                               outline=LIGHT_GOLD, width=3, fill='#fffdfa')
        _fit(draw, label, (left+right)//2, 1390, 603, 29, fill=MUTED, language=language)
        _fit(draw, value, (left+right)//2, 1461, 618, 49, kind='display',
             min_size=27, fill=BLUE, language=language)
    _fit(draw, footer, WIDTH//2, 1593, 1930, 29, fill=MUTED, language=language)
    return image


def image_bytes(content, language='en', file_format='png', logo_path=None):
    image = build_certificate_image(content, language=language, logo_path=logo_path)
    buf = BytesIO()
    if file_format == 'png':
        image.save(buf, format='PNG', optimize=True)
    elif file_format == 'pdf':
        image.save(buf, format='PDF', resolution=212.1, title='Sematec Training Certificate')
    else:
        raise ValueError('Unsupported export format.')
    return buf.getvalue()

#endregion


#region Certificate CRUD and downloads

def _content_from_certificate(certificate):
    register = certificate.register
    return CertificateContent(
        student_name=certificate.student_name or str(register.student),
        course_title=certificate.course_title or register.course.title,
        duration=certificate.course_hours if certificate.course_hours is not None else register.course.duration,
        grade=str(certificate.grade),
        serial_number=certificate.serial_number,
        issue_date=certificate.issue_date,
        student_name_fa=certificate.student_name_fa,
        course_title_fa=certificate.course_title_fa,
    )


def _image_response(data, *, filename=None, content_type='image/png'):
    response = HttpResponse(data, content_type=content_type)
    response['Cache-Control'] = 'private, no-store, max-age=0'
    if filename:
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@role_required('manager')
@never_cache
def certificate_list(request):
    issued = Certificate.objects.select_related('register__student', 'register__course')
    term = request.GET.get('q', '').strip()
    if term:
        from django.db.models import Q
        issued = issued.filter(
            Q(serial_number__icontains=term) |
            Q(student_name__icontains=term) |
            Q(course_title__icontains=term)
        )
    return render(request, 'lms/certificate_list.html', {
        'certificates': issued[:200], 'search_query': term,
        'total_count': Certificate.objects.count(),
    })


def _editor(request, instance=None):
    is_edit = instance is not None
    form = CertificateForm(request.POST or None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        certificate = form.save(commit=False)
        if not is_edit:
            register = certificate.register
            # Freeze the actual recipient and course values at issuance time.
            certificate.student_name = str(register.student)
            certificate.course_title = register.course.title
            certificate.course_hours = register.course.duration
        try:
            certificate.full_clean()
            with transaction.atomic():
                certificate.save()
        except ValidationError as exc:
            form.add_error(None, '; '.join(exc.messages))
        except IntegrityError:
            form.add_error(None, 'The serial or register is already assigned. Please reload and retry.')
        else:
            return redirect(f'{reverse("certificate_edit", args=[certificate.pk])}?saved=1')

    return render(request, 'lms/certificate_form.html', {
        'form': form, 'certificate': instance,
        'is_edit': is_edit,
        'saved': bool(request.GET.get('saved') == '1'),
    })


@role_required('manager')
@never_cache
def certificate_create(request):
    return _editor(request)


@role_required('manager')
@never_cache
def certificate_edit(request, pk):
    certificate = get_object_or_404(Certificate, pk=pk)
    return _editor(request, certificate)

@role_required('manager')
def certificate_delete(request, pk):
    certificate = get_object_or_404(Certificate, pk=pk)
    if request.method == 'POST':
        certificate.delete()
        return redirect('certificate_list')

    return render(request, 'lms/confirm_delete.html', {
        'object': certificate,
        'page_title': 'Delete Certificate',
        'cancel_url': 'certificate_list',
        'delete_note': 'The issued certificate record will be permanently deleted.',
    })


@never_cache
@role_required('manager')
def certificate_courses(request):
    try:
        student_id = int(request.GET.get('student_id', ''))
    except (TypeError, ValueError):
        return JsonResponse({'courses': []})
    if not Student.objects.filter(pk=student_id).exists():
        return JsonResponse({'courses': []})
    registers = Register.objects.filter(student_id=student_id).select_related('course', 'certificate').order_by('course__title')
    result = []
    for register in registers:
        try:
            certificate = register.certificate
        except Certificate.DoesNotExist:
            certificate = None
        result.append({
            'id': register.pk,
            'title': register.course.title,
            'status': register.get_status_display(),
            'dropped': register.status == 'D',
            'issued_id': certificate.pk if certificate else None,
            'serial': certificate.serial_number if certificate else '',
        })
    return JsonResponse({'courses': result})


@role_required('manager')
@never_cache
def certificate_preview(request):
    """Render the CURRENT form fields without requiring a saved certificate.

    Even an incomplete form receives a draft image; only mismatched links,
    obviously invalid numbers or dates are rejected. Save is still validated
    through CertificateForm and model.full_clean() in the editor.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required.'}, status=405)
    language = request.POST.get('language', 'en')
    if language not in ('en', 'fa'):
        return JsonResponse({'error': 'Unknown language.'}, status=400)

    edit_id = request.POST.get('certificate_id', '').strip()
    instance = get_object_or_404(Certificate.objects.select_related(
        'register__student', 'register__course'
    ), pk=edit_id) if edit_id else None

    def optional_pk(key):
        raw = request.POST.get(key, '').strip()
        if not raw:
            return None
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

    student_id, register_id = optional_pk('student'), optional_pk('register')
    if instance:
        student = instance.register.student
        register = instance.register
    else:
        student = Student.objects.filter(pk=student_id).first() if student_id else None
        register = Register.objects.select_related('student', 'course').filter(pk=register_id).first() if register_id else None
        if register and (not student or register.student_id != student.pk):
            return JsonResponse({'error': 'Selected course does not belong to the student.'}, status=422)

    raw_grade = request.POST.get('grade', '').strip()
    if raw_grade:
        try:
            grade_num = Decimal(raw_grade)
            if not grade_num.is_finite() or not (0 <= grade_num <= 100):
                raise ValueError
        except (InvalidOperation, ValueError):
            return JsonResponse({'error': 'Grade must be between 0 and 100.',
                                 'fields': {'grade': ['Enter a number from 0 to 100.']}}, status=422)
    try:
        raw_date = request.POST.get('issue_date', '').strip()
        issued_on = date.fromisoformat(raw_date) if raw_date else timezone.localdate()
    except ValueError:
        return JsonResponse({'error': 'Enter a valid issue date.',
                             'fields': {'issue_date': ['Use YYYY-MM-DD.']}}, status=422)

    title = (instance.course_title if instance else (register.course.title if register else 'Course Title'))
    name = (instance.student_name if instance else (str(student) if student else 'Student Name'))
    hours = (instance.course_hours if instance else (register.course.duration if register else '—'))
    name_fa = request.POST.get('student_name_fa', '').strip()[:150]
    title_fa = request.POST.get('course_title_fa', '').strip()[:150]
    content = CertificateContent(
        student_name=name,
        course_title=title,
        duration=hours,
        grade=raw_grade or '—',
        serial_number=request.POST.get('serial_number', '').strip().upper()[:40] or 'DRAFT',
        issue_date=issued_on,
        student_name_fa=name_fa or ('' if student else 'نام دانشجو'),
        course_title_fa=title_fa or ('' if register else 'عنوان دوره'),
    )
    try:
        img = build_certificate_image(content, language=language)
        img.thumbnail((1200, 850), resample=Image.Resampling.LANCZOS)
        output = BytesIO()
        img.save(output, format='PNG', optimize=True)
    except (RuntimeError, ValueError, OSError) as exc:
        return JsonResponse({'error': f'Preview error: {exc}'}, status=503)
    return _image_response(output.getvalue())


@role_required('manager')
@never_cache
def certificate_download(request, pk, language, file_format):
    if language not in ('en', 'fa') or file_format not in ('png', 'pdf'):
        return JsonResponse({'error': 'Unsupported language or format.'}, status=404)
    certificate = get_object_or_404(Certificate.objects.select_related(
        'register__student', 'register__course'
    ), pk=pk)
    try:
        data = image_bytes(_content_from_certificate(certificate), language=language, file_format=file_format)
    except (RuntimeError, OSError) as exc:
        return HttpResponse(f'Certificate could not be rendered: {exc}', status=503, content_type='text/plain')
    media_type = 'application/pdf' if file_format == 'pdf' else 'image/png'
    safe_serial = certificate.serial_number.replace('/', '-')
    return _image_response(data, filename=f'sematec-{safe_serial}-{language}.{file_format}',
                           content_type=media_type)

#endregion

#region Survey

@role_required('manager', 'instructor')
def survey_dashboard(request):
    courses = _visible_courses(request).order_by('title')
    summary = []
    for course in courses:
        answers = SurveyAnswer.objects.filter(response__course=course)
        if not is_manager(request.user):
            answers = answers.filter(response__audience='I', response__instructor=_instructor_for(request))
        aggregates = answers.aggregate(average=Avg('rating'), count=Count('id'))
        summary.append({'course': course, **aggregates})
    return render(request, 'lms/survey_dashboard.html', {
        'summary': summary,
        'student_questions': SurveyQuestion.objects.filter(audience='S', active=True).count(),
        'instructor_questions': SurveyQuestion.objects.filter(audience='I', active=True).count(),
    })


@role_required('manager')
def survey_questions(request):
    action = request.POST.get('action') if request.method == 'POST' else ''
    if action == 'toggle':
        question = get_object_or_404(SurveyQuestion, pk=request.POST.get('question'), archived=False)
        question.active = not question.active
        question.save(update_fields=['active'])
        return redirect('survey_questions')
    form = SurveyQuestionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('survey_questions')
    return render(request, 'lms/survey_questions.html', {
        'form': form,
        'questions': SurveyQuestion.objects.filter(archived=False),
    })


@role_required('manager')
def survey_question_edit(request, pk):
    question = get_object_or_404(SurveyQuestion, pk=pk, archived=False)
    form = SurveyQuestionForm(request.POST or None, instance=question)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('survey_questions')
    return render(request, 'lms/survey_questions.html', {
        'form': form,
        'editing_question': question,
        'questions': SurveyQuestion.objects.filter(archived=False),
    })


@role_required('manager')
def survey_question_delete(request, pk):
    question = get_object_or_404(SurveyQuestion, pk=pk, archived=False)
    has_answers = question.answers.exists()
    if request.method == 'POST':
        if has_answers:
            # Soft deletion retains historical student/instructor assessments.
            question.archived = True
            question.active = False
            question.save(update_fields=['archived', 'active'])
        else:
            question.delete()
        return redirect('survey_questions')
    return render(request, 'lms/confirm_delete.html', {
        'object': question,
        'page_title': _('Delete survey question'),
        'cancel_url': 'survey_questions',
        'delete_note': (_('Existing answers will be preserved and the question will be archived.')
                        if has_answers else _('This question has no saved answers and will be deleted.')),
    })


@role_required('manager', 'instructor')
def survey_course(request, course_id):
    course = get_object_or_404(_visible_courses(request), pk=course_id)
    instructors = Instructor.objects.filter(schedules__course=course).distinct().order_by('last_name')
    if not is_manager(request.user):
        instructors = instructors.filter(pk=_instructor_for(request).pk)
    registers = _visible_registers(request).filter(course=course).select_related('student', 'instructor')
    responses = SurveyResponse.objects.filter(course=course).annotate(average_rating=Avg('answers__rating'))
    if not is_manager(request.user):
        responses = responses.filter(audience='I', instructor=_instructor_for(request))
    return render(request, 'lms/survey_course.html', {
        'course': course, 'instructors': instructors,
        'registers': registers if is_manager(request.user) else [],
        'responses': responses,
        'is_manager': is_manager(request.user),
    })


@role_required('manager', 'instructor')
def survey_respond(request, course_id, audience, person_id):
    course = get_object_or_404(_visible_courses(request), pk=course_id)
    if audience == 'I':
        instructor = get_object_or_404(Instructor.objects.filter(schedules__course=course).distinct(), pk=person_id)
        if not is_manager(request.user) and instructor.pk != _instructor_for(request).pk:
            raise PermissionDenied('You can only submit your own instructor survey.')
        register = None
        identity = instructor
        lookup = {'course': course, 'instructor': instructor}
    elif audience == 'S':
        if not is_manager(request.user):
            raise PermissionDenied('Student responses are recorded by education managers.')
        register = get_object_or_404(Register, course=course, pk=person_id)
        instructor = None
        identity = register.student
        lookup = {'course': course, 'register': register}
    else:
        return HttpResponseBadRequest('Unknown questionnaire type.')
    questions = list(SurveyQuestion.objects.filter(audience=audience, active=True))
    existing = SurveyResponse.objects.filter(**lookup).first()
    current = {a.question_id: a.rating for a in existing.answers.all()} if existing else {}
    error = ''
    if request.method == 'POST':
        if not questions:
            error = 'No active survey questions are configured for this audience.'
        else:
            answers = {}
            for question in questions:
                raw = request.POST.get(f'question_{question.pk}', '')
                if raw not in ('1', '2', '3', '4', '5'):
                    error = 'Please rate every question from 1 to 5.'
                    break
                answers[question.pk] = int(raw)
            if not error:
                with transaction.atomic():
                    if existing:
                        response = existing
                        response.recorded_by = request.user
                        response.save(update_fields=['recorded_by', 'updated_at'])
                    else:
                        response = SurveyResponse(audience=audience, recorded_by=request.user, **lookup)
                        response.full_clean()
                        response.save()
                    for question_id, rating in answers.items():
                        SurveyAnswer.objects.update_or_create(
                            response=response, question_id=question_id,
                            defaults={'rating': rating},
                        )
                return redirect('survey_course', course_id=course.pk)
            current = {q.pk: request.POST.get(f'question_{q.pk}') for q in questions}
    question_rows = [{'question': q, 'rating': str(current.get(q.pk, ''))} for q in questions]
    return render(request, 'lms/survey_respond.html', {
        'course': course, 'audience': audience,
        'identity': identity, 'questions': question_rows, 'error': error,
        'is_manager': is_manager(request.user),
    })


@role_required('manager')
def survey_results(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    responses = SurveyResponse.objects.filter(course=course).select_related('instructor', 'register__student').annotate(
        average_rating=Avg('answers__rating')).order_by('audience', '-updated_at')
    question_rows = SurveyQuestion.objects.filter(answers__response__course=course).distinct().annotate(
        average_rating=Avg('answers__rating', filter=Q(answers__response__course=course)),
        count=Count('answers', filter=Q(answers__response__course=course)),
    ).order_by('audience', 'position')
    summary = SurveyAnswer.objects.filter(response__course=course).values('response__audience').annotate(
        average=Avg('rating'), count=Count('id'))
    return render(request, 'lms/survey_results.html', {
        'course': course, 'responses': responses, 'question_rows': question_rows,
        'summary': summary,
    })

#endregion