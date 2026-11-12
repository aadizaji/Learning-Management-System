from django.db import models
from datetime import date
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class Student(models.Model):
    def __str__(self):
        return f'{self.first_name} {self.last_name}'
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    profile_img = models.ImageField(upload_to='students/', blank=True, null=True)
    father_name = models.CharField(max_length=100)
    national_code = models.CharField(max_length=10, unique=True)
    birth_date = models.DateField()
    GENDER_CHOICES = (
        ('M', _('Male')),
        ('F', _('Female'))
    )
    gender = models.CharField(choices=GENDER_CHOICES, max_length=1)
    work_place = models.CharField(max_length=100)
    # Formerly job_position. Keep the existing values when migrating.
    job_title = models.CharField(_('Job title'), max_length=180, blank=True)
    ORGANIZATIONAL_POSITION_CHOICES = (
        ('employee', _('Employee')),
        ('worker', _('Worker')),
        ('associate', _('Technical associate')),
        ('technician', _('Technician')),
        ('specialist', _('Specialist')),
        ('officer', _('Officer')),
        ('head', _('Head')),
        ('manager', _('Manager')),
        ('ceo', _('CEO')),
        ('other', _('Other')),
    )
    organizational_position = models.CharField(
        _('Organizational position'), max_length=16,
        choices=ORGANIZATIONAL_POSITION_CHOICES, blank=True,
    )
    EDUCATIONAL_CHOICES = (
        ('D', _('Diploma')),
        ('A', _('Associate degree')),
        ('B', _('Bachelor')),
        ('M', _('Master')),
        ('P', _('Ph.D')),
    )
    educational_certification = models.CharField(
        _('Educational Certification'), choices=EDUCATIONAL_CHOICES,
        max_length=1, blank=True,
    )
    phone_number = models.CharField(max_length=11)
    email = models.EmailField()
    city = models.CharField(max_length=50)
    address = models.TextField()

class Instructor(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='instructor_profile')

    def __str__(self):
        return f'{self.first_name} {self.last_name}'
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    profile_img = models.ImageField(upload_to='instructors/', blank=True, null=True)
    national_code = models.CharField(max_length=10, unique=True)
    birth_date = models.DateField()
    GENDER_CHOICES = (
        ('M', _('Male')),
        ('F', _('Female')),
    )
    gender = models.CharField(choices=GENDER_CHOICES, max_length=1)
    EDUCATIONAL_CHOICES = (
        ('D', _('Diploma')),
        ('A', _('Associate degree')),
        ('B', _('Bachelor')),
        ('M', _('Master')),
        ('P', _('Ph.D')),
    )
    educational_certification = models.CharField(choices=EDUCATIONAL_CHOICES, max_length=1)
    phone_number = models.CharField(max_length=11)
    email = models.EmailField()
    city = models.CharField(max_length=50)
    address = models.TextField()

class CourseCategory(models.Model):
    def __str__(self):
        return self.name
    name = models.CharField(max_length=100)

class Course(models.Model):
    def __str__(self):
        return self.title
    title = models.CharField(max_length=100)
    poster = models.ImageField(upload_to='courses/', blank=True, null=True)
    course_category = models.ForeignKey(CourseCategory, on_delete=models.CASCADE)
    instructors = models.ManyToManyField(Instructor)
    duration = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    capacity = models.IntegerField()
    LEVEL_CHOICES = (
        ('A', _('Beginner')),
        ('B', _('Advanced')),
        ('C', _('Comprehensive')),
    )
    course_level = models.CharField(choices=LEVEL_CHOICES, max_length=1)
    STATUS_CHOICES = (
        ('A', _('Active')),
        ('B', _('Inactive')),
        ('C', _('In Progress')),
        ('D', _('Coming Soon ...')),
    )
    course_status = models.CharField(choices=STATUS_CHOICES, max_length=1)
    DELIVERY_MODE_CHOICES = (
        ('P', _('In person')),
        ('R', _('Remote')),
        ('H', _('In person and remote')),
    )
    delivery_mode = models.CharField(
        _('Delivery mode'), max_length=1, choices=DELIVERY_MODE_CHOICES, default='P'
    )
    description = models.TextField()
    price = models.IntegerField()

    @property
    def formatted_price(self):
        """Display only; the database keeps a plain integer amount in toman."""
        return f'{self.price:,} (تومان)' if self.price is not None else '—'

class CourseSchedule(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='schedules')
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, related_name='schedules')
    WEEKDAYS_CHOICES = (
        (0, _('Saturday')),
        (1, _('Sunday')),
        (2, _('Monday')),
        (3, _('Tuesday')),
        (4, _('Wednesday')),
        (5, _('Thursday')),
        (6, _('Friday')),
    )
    weekday = models.IntegerField(choices=WEEKDAYS_CHOICES)
    classroom = models.CharField(max_length=30, blank=True, default='')  # Legacy schedules may have no room
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return (
            f'{self.course.title} - '
            f'{self.get_weekday_display()} - '
            f'{self.start_time:%H:%M} / Room {self.classroom or "—"}'
        )

    def clean(self):
        super().clean()
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError({
                    'end_time': 'End time must be after start time.'
                })

        if self.course_id and self.instructor_id:
            if not self.course.instructors.filter(
                    pk=self.instructor_id
            ).exists():
                raise ValidationError({
                    'instructor': 'This instructor does not belong to the selected course.'
                })

        # Prevent two courses occupying the same room, or one instructor
        # teaching two courses, on an overlapping date range and weekly slot.
        if self.course_id and self.weekday is not None and self.start_time and self.end_time:
            course = self.course
            clashes = CourseSchedule.objects.filter(
                weekday=self.weekday,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time,
                course__start_date__lte=course.end_date,
                course__end_date__gte=course.start_date,
            ).exclude(pk=self.pk)
            if self.classroom and clashes.filter(classroom__iexact=self.classroom.strip()).exists():
                raise ValidationError({'classroom': 'This classroom is occupied at that time.'})
            if self.instructor_id and clashes.filter(instructor_id=self.instructor_id).exists():
                raise ValidationError({'instructor': 'This instructor has another class at that time.'})

class CourseTopic(models.Model):
    course = models.ForeignKey(Course, related_name='topics', on_delete=models.CASCADE)
    title = models.CharField(max_length=220)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['position', 'pk']

    def __str__(self):
        return self.title

class Register(models.Model):
    def __str__(self):
        return f'{self.student} - {self.course}'

    student = models.ForeignKey(Student,on_delete=models.CASCADE)
    course = models.ForeignKey(Course,on_delete=models.CASCADE)
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE)
    register_date = models.DateField(auto_now_add=True)
    completed_on = models.DateField(null=True, blank=True)

    STATUS_CHOICES = (
        ('A', _('Active')),
        ('C', _('Completed')),
        ('D', _('Dropped')),
    )

    status = models.CharField(choices=STATUS_CHOICES,max_length=1)

class ClassSession(models.Model):

    STATUS_CHOICES = (
        ('S', _('Scheduled')),
        ('C', _('Completed')),
        ('X', _('Cancelled')),
    )

    # PROTECT preserves historical sessions when weekly schedules are edited.
    course_schedule = models.ForeignKey(
        CourseSchedule, on_delete=models.PROTECT, related_name='sessions'
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='S')
    cancellation_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['date', 'start_time', 'pk']
        constraints = [
            models.UniqueConstraint(
                fields=['course_schedule', 'date'],
                name='unique_course_schedule_date',
            ),
        ]

    def __str__(self):
        return f'{self.course_schedule.course.title} - {self.date}'

    def clean(self):
        super().clean()
        errors = {}
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            errors['end_time'] = 'End time must be after start time.'
        if self.status == 'X' and not (self.cancellation_reason or '').strip():
            errors['cancellation_reason'] = 'A cancellation reason is required.'
        if errors:
            raise ValidationError(errors)

class Attendance(models.Model):

    STATUS_CHOICES = (
        ('P', _('Present')),
        ('A', _('Absent')),
    )
    session = models.ForeignKey(
        ClassSession, on_delete=models.PROTECT, related_name='attendance_records'
    )
    register = models.ForeignKey(
        Register, on_delete=models.PROTECT, related_name='attendance_records'
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    recorded_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['session', 'register'], name='unique_session_register'
            ),
        ]
        ordering = ['register__student__last_name', 'register__student__first_name']

    def __str__(self):
        return f'{self.register.student} - {self.session.date} - {self.get_status_display()}'

    def clean(self):
        super().clean()
        errors = {}
        if self.session_id and self.register_id:
            if self.register.course_id != self.session.course_schedule.course_id:
                errors['register'] = 'Student register must belong to the session course.'
            if self.session.status == 'X':
                errors['session'] = 'Attendance cannot be recorded for a cancelled session.'
        if errors:
            raise ValidationError(errors)

class Certificate(models.Model):

    register = models.OneToOneField(
        Register, on_delete=models.PROTECT, related_name='certificate'
    )
    serial_number = models.CharField(max_length=40, unique=True)
    grade = models.DecimalField(max_digits=5, decimal_places=2)
    issue_date = models.DateField(default=date.today)
    student_name = models.CharField(max_length=220)
    course_title = models.CharField(max_length=220)
    course_hours = models.PositiveIntegerField()
    student_name_fa = models.CharField(max_length=220, blank=True)
    course_title_fa = models.CharField(max_length=220, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-issue_date', '-pk']

    def __str__(self):
        return f'{self.serial_number} - {self.student_name} / {self.course_title}'

    def clean(self):
        super().clean()
        errors = {}
        if self.grade is not None and not (0 <= self.grade <= 100):
            errors['grade'] = 'Grade must be from 0 to 100.'
        if self.register_id and self._state.adding:
            if self.register.status == 'D':
                errors['register'] = 'Dropped registers cannot receive new certificates.'
            # The form normally prevents duplicate Register records, but
            # admin/script imports could have created them historically.
            if Certificate.objects.filter(
                register__student_id=self.register.student_id,
                register__course_id=self.register.course_id,
            ).exists():
                errors['register'] = 'This student already has a certificate for this course.'
        if errors:
            raise ValidationError(errors)

class Exam(models.Model):

    TYPE_CHOICES = (('O', _('Online')), ('F', _('Offline')))
    title = models.CharField(max_length=160)
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name='exams')
    exam_type = models.CharField(max_length=1, choices=TYPE_CHOICES, default='F')
    exam_date = models.DateField()
    max_score = models.DecimalField(max_digits=6, decimal_places=2, default=100)
    passing_score = models.DecimalField(max_digits=6, decimal_places=2, default=70)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['-exam_date', '-pk']

    def __str__(self):
        return f'{self.title} - {self.course.title}'

    def clean(self):
        super().clean()
        errors = {}
        if self.max_score is not None and self.max_score <= 0:
            errors['max_score'] = 'Maximum score must be greater than zero.'
        if self.passing_score is not None and self.max_score is not None:
            if not (0 <= self.passing_score <= self.max_score):
                errors['passing_score'] = 'Passing score must be between zero and the maximum score.'
        if errors:
            raise ValidationError(errors)

class ExamGrade(models.Model):

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='grades')
    register = models.ForeignKey(Register, on_delete=models.PROTECT, related_name='exam_grades')
    score = models.DecimalField(max_digits=6, decimal_places=2)
    written_score = models.DecimalField(_('Written score'), max_digits=6, decimal_places=2, null=True, blank=True)
    practical_score = models.DecimalField(_('Practical/project score'), max_digits=6, decimal_places=2, null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['register__student__last_name', 'register__student__first_name']
        constraints = [models.UniqueConstraint(fields=['exam', 'register'], name='unique_exam_register')]

    @property
    def passed(self):
        return self.score >= self.exam.passing_score

    def __str__(self):
        return f'{self.register.student} - {self.exam.title}: {self.score}'

    def clean(self):
        super().clean()
        errors = {}
        if self.exam_id and self.register_id and self.exam.course_id != self.register.course_id:
            errors['register'] = 'The student must be registered in the exam course.'
        if self.exam_id and self.score is not None and (not self.score.is_finite() or not (0 <= self.score <= self.exam.max_score)):
            errors['score'] = 'Score must be between zero and the maximum score.'
        for field_name in ('written_score', 'practical_score'):
            value = getattr(self, field_name)
            if self.exam_id and value is not None and (not value.is_finite() or not (0 <= value <= self.exam.max_score)):
                errors[field_name] = 'The component score must be between zero and the maximum score.'
        if errors:
            raise ValidationError(errors)

class SurveyQuestion(models.Model):
    AUDIENCE_CHOICES = (('I', _('Instructor')), ('S', _('Student')))
    audience = models.CharField(max_length=1, choices=AUDIENCE_CHOICES)
    title = models.CharField(max_length=320)
    position = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    # A deleted question with existing answers is archived to preserve evaluations.
    archived = models.BooleanField(default=False)

    class Meta:
        ordering = ('audience', 'position', 'pk')

    def __str__(self):
        return f'{self.get_audience_display()}: {self.title}'

class SurveyResponse(models.Model):
    course = models.ForeignKey(Course, related_name='survey_responses', on_delete=models.PROTECT)
    audience = models.CharField(max_length=1, choices=SurveyQuestion.AUDIENCE_CHOICES)
    instructor = models.ForeignKey(Instructor, null=True, blank=True, related_name='survey_responses', on_delete=models.PROTECT)
    register = models.ForeignKey(Register, null=True, blank=True, related_name='survey_responses', on_delete=models.PROTECT)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('course', 'instructor'), name='survey_unique_instructor_course'),
            models.UniqueConstraint(fields=('course', 'register'), name='survey_unique_register_course'),
        ]

    def clean(self):
        super().clean()
        if self.audience == 'I':
            if not self.instructor_id or self.register_id:
                raise ValidationError('Instructor evaluation requires only an instructor.')
            if self.course_id and self.instructor_id and not self.course.schedules.filter(instructor_id=self.instructor_id).exists():
                raise ValidationError('The instructor must teach this course.')
        elif self.audience == 'S':
            if not self.register_id or self.instructor_id:
                raise ValidationError('Student evaluation requires only a course register.')
            if self.course_id and self.register_id and self.register.course_id != self.course_id:
                raise ValidationError('The student registration belongs to another course.')
        else:
            raise ValidationError('Invalid survey audience.')

    def __str__(self):
        return f'{self.course} - {self.instructor or self.register}'

class SurveyAnswer(models.Model):
    response = models.ForeignKey(SurveyResponse, related_name='answers', on_delete=models.CASCADE)
    question = models.ForeignKey(SurveyQuestion, related_name='answers', on_delete=models.PROTECT)
    rating = models.PositiveSmallIntegerField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=('response', 'question'), name='survey_unique_answer')]

    def clean(self):
        super().clean()
        if not 1 <= self.rating <= 5:
            raise ValidationError({'rating': 'Rating must be between 1 and 5.'})
        if self.response_id and self.question_id and self.response.audience != self.question.audience:
            raise ValidationError({'question': 'Question audience does not match the response.'})