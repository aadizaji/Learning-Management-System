from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    # Directory pages and read-only profiles
    path('students/', views.student_list, name='student_list'),
    path('students/<int:pk>/', views.student_detail, name='student_detail'),
    path('instructors/', views.instructor_list, name='instructor_list'),
    path('instructors/<int:pk>/', views.instructor_detail, name='instructor_detail'),
    path('courses/', views.course_list, name='course_list'),
    path('courses/<int:pk>/', views.course_detail, name='course_detail'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/<int:pk>/', views.category_detail, name='category_detail'),
    path('registers/', views.register_list, name='register_list'),
    path('reports/<str:section>/csv/', views.report_csv, name='report_csv'),
    # Exam management (inside the LMS, without using Django Admin)
    path('exams/', views.exam_list, name='exam_list'),
    path('exams/add/', views.add_exam, name='add_exam'),
    path('exams/<int:pk>/', views.exam_detail, name='exam_detail'),
    path('exams/<int:pk>/edit/', views.edit_exam, name='edit_exam'),
    path('exams/<int:pk>/delete/', views.delete_exam, name='delete_exam'),
    path('exams/<int:pk>/grades/', views.exam_grades, name='exam_grades'),
    path('exams/<int:pk>/grades/csv/', views.exam_grades_csv, name='exam_grades_csv'),

    # Students
    path('students/add/', views.add_student, name='add_student'),
    path('students/<int:pk>/edit/', views.edit_student, name='edit_student'),
    path('students/<int:pk>/delete/', views.delete_student, name='delete_student'),
    path('instructors/add/', views.add_instructor, name='add_instructor'),
    path('instructor/<int:pk>/edit/', views.edit_instructor, name='edit_instructor'),
    path('instructor/<int:pk>/delete/', views.delete_instructor, name='delete_instructor'),
    path('courses/add/', views.add_course, name='add_course'),
    path('courses/<int:pk>/edit/', views.edit_course, name='edit_course'),
    path('courses/<int:pk>/delete/', views.delete_course, name='delete_course'),
    path('coursecategory/add/', views.add_course_category, name='add_course_category'),
    path('coursecategory/<int:pk>/edit/', views.edit_course_category, name='edit_course_category'),
    path('coursecategory/<int:pk>/delete/', views.delete_course_category, name='delete_course_category'),
    path('registers/add/', views.add_register, name='add_register'),
    path('registers/<int:pk>/edit/', views.edit_register, name='edit_register'),
    path('registers/<int:pk>/delete/', views.delete_register, name='delete_register'),
    path('calendar/', views.academic_calendar, name='academic_calendar'),
    path('attendance/', views.attendance_dashboard, name='attendance_dashboard'),
    path('attendance/sessions/<int:session_id>/csv/', views.attendance_session_csv, name='attendance_session_csv'),
    path('attendance/courses/<int:course_id>/csv/', views.attendance_course_csv, name='attendance_course_csv'),
    # Training certificates: staff-only issue, preview, edit and export.
    path('certificates/', views.certificate_list, name='certificate_list'),
    path('certificates/new/', views.certificate_create, name='certificate_create'),
    path('certificates/<int:pk>/edit/', views.certificate_edit, name='certificate_edit'),
    path('certificates/student-courses/', views.certificate_courses, name='certificate_courses'),
    path('certificates/preview/', views.certificate_preview, name='certificate_preview'),
    path('certificates/<int:pk>/download/<str:language>/<str:file_format>/',
         views.certificate_download, name='certificate_download'),
    path('certificates/<int:pk>/delete/',views.certificate_delete,name='certificate_delete'),
    # Survey questionnaires, class-linked responses and evaluations.
    path('surveys/', views.survey_dashboard, name='survey_dashboard'),
    path('surveys/questions/', views.survey_questions, name='survey_questions'),
    path('surveys/questions/<int:pk>/edit/', views.survey_question_edit, name='survey_question_edit'),
    path('surveys/questions/<int:pk>/delete/', views.survey_question_delete, name='survey_question_delete'),
    path('surveys/courses/<int:course_id>/', views.survey_course, name='survey_course'),
    path('surveys/courses/<int:course_id>/respond/<str:audience>/<int:person_id>/', views.survey_respond, name='survey_respond'),
    path('surveys/courses/<int:course_id>/results/', views.survey_results, name='survey_results'),
    path('calender/', views.legacy_calendar_redirect, name='legacy_calendar'),

    path(
        'courses/<int:course_id>/instructors/',
        views.get_course_instructors,
        name='get_course_instructors'
    ),

]