from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Student)
admin.site.register(Instructor)
admin.site.register(CourseCategory)
admin.site.register(Course)
admin.site.register(Register)
admin.site.register(CourseSchedule)
admin.site.register(CourseTopic)




@admin.register(ClassSession)
class ClassSessionAdmin(admin.ModelAdmin):
    list_display = ('course_schedule', 'date', 'start_time', 'end_time', 'status')
    list_filter = ('status', 'date', 'course_schedule__course')
    search_fields = ('course_schedule__course__title', 'course_schedule__instructor__last_name')


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('session', 'register', 'status', 'recorded_at')
    list_filter = ('status', 'session__course_schedule__course')
    search_fields = ('register__student__first_name', 'register__student__last_name')
    readonly_fields = ('recorded_at',)


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('serial_number', 'student_name', 'course_title', 'grade', 'issue_date')
    search_fields = ('serial_number', 'student_name', 'course_title', 'register__student__national_code')
    list_filter = ('issue_date',)
    readonly_fields = (
        'register', 'serial_number', 'grade', 'issue_date',
        'student_name', 'course_title', 'course_hours',
        'student_name_fa', 'course_title_fa', 'created_at', 'updated_at',
    )

    def has_add_permission(self, request):
        # Creation must use the certificate form so snapshot fields are saved.
        return False

    def has_delete_permission(self, request, obj=None):
        # Keep the historical issued record intact.
        return False



@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'exam_type', 'exam_date', 'max_score', 'passing_score')
    search_fields = ('title', 'course__title')
    list_filter = ('exam_type', 'exam_date')


@admin.register(ExamGrade)
class ExamGradeAdmin(admin.ModelAdmin):
    list_display = ('exam', 'register', 'score', 'recorded_at')
    list_filter = ('exam__course',)


@admin.register(SurveyQuestion)
class SurveyQuestionAdmin(admin.ModelAdmin):
    list_display = ('title', 'audience', 'position', 'active')
    list_filter = ('audience', 'active')
    search_fields = ('title',)


@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = ('course', 'audience', 'instructor', 'register', 'updated_at')
    list_filter = ('audience', 'course')


@admin.register(SurveyAnswer)
class SurveyAnswerAdmin(admin.ModelAdmin):
    list_display = ('response', 'question', 'rating')
