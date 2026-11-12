from django.utils.translation import gettext_lazy as _
from django import forms
import re
from datetime import date
from django.forms import ModelForm, BaseInlineFormSet, inlineformset_factory
from django.core.exceptions import ValidationError
from .models import Student, Instructor, Course, CourseCategory, Register, CourseSchedule, CourseTopic, Exam, Certificate, SurveyQuestion



def date_widget():
    return forms.DateInput(
        format='%Y-%m-%d',
        attrs={'type': 'date', 'class': 'js-date-input', 'placeholder': 'YYYY-MM-DD'}, # HTML
    )


class LocalizedModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):  #مقدار دهی اولیه فرم ها
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if field.label:
                field.label = _(field.label) # Translate
            if hasattr(field, 'empty_label') and field.empty_label:
                field.empty_label = _(field.empty_label)


class NewStudentForm(LocalizedModelForm):
    class Meta:
        model = Student
        fields = '__all__'
        widgets = {
            'birth_date': date_widget(),
            'job_title': forms.TextInput(attrs={'placeholder': _('Enter the job title'), 'maxlength': '180'}),
            'organizational_position': forms.Select(),
        }

class NewInstructorForm(LocalizedModelForm):
    class Meta:
        model = Instructor
        exclude = ('user',)
        widgets = {'birth_date': date_widget()}


class NewCourseForm(LocalizedModelForm):
    price = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'js-price-input', 'inputmode': 'numeric', 'autocomplete': 'off',
        'placeholder': '0', 'dir': 'ltr',
    }))


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound and self.instance.pk:
            self.initial['price'] = f'{self.instance.price:,}'

    def clean_price(self):
        raw = str(self.cleaned_data.get('price', '')).strip()
        digits = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')
        normalized = raw.translate(digits).replace(',', '').replace('٬', '').replace('،', '').replace(' ', '')
        if not normalized.isdecimal():
            raise ValidationError(_('Enter a valid non-negative price in toman.'))
        value = int(normalized)
        if value > 2147483647:
            raise ValidationError(_('Price is too large.'))
        return value

    class Meta:
        model = Course
        fields = [
            'title', 'poster', 'course_category', 'instructors', 'duration',
            'start_date', 'end_date', 'capacity', 'course_level',
            'course_status', 'delivery_mode', 'description', 'price',
        ]
        widgets = {
            'start_date': date_widget(),
            'end_date': date_widget(),
        }

    def clean(self):
        data = super().clean()
        start_date, end_date = data.get('start_date'), data.get('end_date')
        if start_date and end_date and start_date > end_date:
            self.add_error('end_date', 'End date must be on or after the start date.')
        return data


class CourseScheduleForm(LocalizedModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['classroom'].required = not bool(self.instance.pk)
        self.fields['classroom'].widget.attrs.update({'placeholder': '101', 'maxlength': '30'})

    class Meta:
        model = CourseSchedule
        fields = ('instructor', 'weekday', 'classroom', 'start_time', 'end_time')
        widgets = {
            'start_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
            'end_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
        }


class BaseCourseScheduleFormSet(BaseInlineFormSet): # Validation
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        slots = []
        for form in self.forms:
            if form.cleaned_data.get('DELETE') and form.instance.pk and form.instance.sessions.exists():
                raise ValidationError(
                    'A weekly schedule with actual sessions cannot be deleted. '
                    'Keep the schedule to preserve class history.'
                )
            if not form.cleaned_data or form.cleaned_data.get('DELETE'):
                continue
            d = form.cleaned_data
            if form.instance.pk and form.instance.sessions.exists() and any(
                name in form.changed_data for name in ('instructor', 'weekday', 'start_time', 'end_time')
            ):
                raise ValidationError(
                    'You cannot change the day, instructor, or time of a schedule with existing sessions. '
                    'Add another weekly schedule instead.'
                )
            instructor = d.get('instructor')
            weekday = d.get('weekday')
            start = d.get('start_time')
            end = d.get('end_time')

            if instructor is None or weekday is None or not start or not end:
                continue
            room = (d.get('classroom') or '').strip().casefold()
            for other in slots:
                if other[1] == weekday and start < other[3] and end > other[2]:
                    if other[0] == instructor.pk:
                        raise ValidationError('Overlapping class times for the same instructor and weekday.')
                    if room and room == other[4]:
                        raise ValidationError('Two classes cannot use the same room at the same time.')
            slots.append((instructor.pk, weekday, start, end, room))
        if getattr(self, 'require_start_weekday', False) and self.instance.start_date:
            start_day = (self.instance.start_date.weekday() + 2) % 7
            if not any(slot[1] == start_day for slot in slots):
                raise ValidationError(_('At least one weekly class must take place on the course start day.'))


CourseScheduleFormSet = inlineformset_factory(
    Course, CourseSchedule, form=CourseScheduleForm,
    formset=BaseCourseScheduleFormSet,
    extra=1, can_delete=True, min_num=1, validate_min=True,
)

class CourseTopicForm(LocalizedModelForm):
    class Meta:
        model = CourseTopic
        fields = ('title',)
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': _('Add a course topic'), 'maxlength': '220'}),
        }


CourseTopicFormSet = inlineformset_factory(
    Course, CourseTopic, form=CourseTopicForm,
    extra=1, can_delete=True,
)


class NewCourseCategoryForm(LocalizedModelForm):
    class Meta:
        model = CourseCategory
        fields = '__all__'

class NewRegisterForm(LocalizedModelForm):
    class Meta:
        model = Register
        fields = ['student', 'course', 'instructor', 'status', 'completed_on']
        widgets = {'completed_on': date_widget()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


        if 'course' in self.data:
            try:
                course_id = int(self.data.get('course'))
                course = Course.objects.get(pk=course_id)
                self.fields['instructor'].queryset = course.instructors.all()
            except (ValueError, TypeError, Course.DoesNotExist):
                self.fields['instructor'].queryset = Instructor.objects.none()
        elif self.instance.pk and self.instance.course_id:
            self.fields['instructor'].queryset = self.instance.course.instructors.all()
        else:
            self.fields['instructor'].queryset = Instructor.objects.none()

    def clean(self):
        cleaned_data = super().clean()

        student = cleaned_data.get('student')
        course = cleaned_data.get('course')
        instructor = cleaned_data.get('instructor')
        status = cleaned_data.get('status')
        if cleaned_data.get('completed_on') and status != 'C':
            self.add_error('completed_on', _('A completion date is only valid for a completed register.'))

        if course and instructor and not course.instructors.filter(pk=instructor.pk).exists():
            self.add_error(
                'instructor',
                'This instructor does not teach the selected course.'
            )

        if student and course:
            duplicate_qs = Register.objects.filter(student=student, course=course)
            if self.instance.pk:
                duplicate_qs = duplicate_qs.exclude(pk=self.instance.pk)
            if duplicate_qs.exists():
                self.add_error(
                    'student',
                    'This student is already registered in this course.'
                )

        if course and status == 'A':
            active_qs = Register.objects.filter(course=course, status='A')
            if self.instance.pk:
                active_qs = active_qs.exclude(pk=self.instance.pk)
            if active_qs.count() >= course.capacity:
                self.add_error(
                    'course',
                    f'This course has reached its capacity ({course.capacity} students).'
                )

        return cleaned_data

class ExamForm(LocalizedModelForm):
    class Meta:
        model = Exam
        fields = ('title', 'course', 'exam_type', 'exam_date', 'max_score', 'passing_score', 'description')
        widgets = {
            'exam_date': date_widget(),
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class CertificateForm(LocalizedModelForm):
    student = forms.ModelChoiceField(queryset=Student.objects.all().order_by('last_name','first_name'))
    register = forms.ModelChoiceField(queryset=Register.objects.none(), label='Registered course')

    class Meta:
        model = Certificate
        fields = (
            'student', 'register', 'grade', 'serial_number', 'issue_date',
            'student_name_fa', 'course_title_fa',
        )
        widgets = {
            'grade': forms.NumberInput(attrs={'min': '0', 'max': '100', 'step': '0.01', 'placeholder': 'e.g. 92.5'}),
            'serial_number': forms.TextInput(attrs={'maxlength': '40', 'placeholder': 'SEM-2026-001', 'autocomplete': 'off'}),
            'issue_date': date_widget(),
            'student_name_fa': forms.TextInput(attrs={'dir': 'rtl', 'placeholder': 'نام دانشجو (اختیاری)'}),
            'course_title_fa': forms.TextInput(attrs={'dir': 'rtl', 'placeholder': 'عنوان دوره (اختیاری)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student'].empty_label = _('Select a student')
        self.fields['register'].empty_label = _('Select a registered course')
        self.fields['student_name_fa'].required = False
        self.fields['course_title_fa'].required = False
        if not self.is_bound and not self.instance.pk:
            self.initial['issue_date'] = date.today()

        student_id = self.data.get('student') if self.is_bound else self.initial.get('student')
        if not student_id and self.instance.pk:
            student_id = self.instance.register.student_id
            self.initial['student'] = student_id
            self.initial['register'] = self.instance.register_id
        if student_id:
            try:
                student_id = int(student_id)
                qs = Register.objects.filter(student_id=student_id).select_related('course')
                if not self.instance.pk:
                    qs = qs.exclude(status='D')
                self.fields['register'].queryset = qs.order_by('course__title', 'pk')
                self.fields['register'].label_from_instance = (
                    lambda e: f'{e.course.title}  ·  {e.get_status_display()}'
                )
            except (TypeError, ValueError):
                pass
        if self.instance.pk:
            # No changing the student/course on an already-issued certificate.
            self.fields['student'].disabled = True
            self.fields['register'].disabled = True

    def clean_serial_number(self):
        serial = (self.cleaned_data.get('serial_number') or '').strip().upper()
        if not re.fullmatch(r'[A-Z0-9][A-Z0-9/-]{2,39}', serial):
            raise ValidationError('Use 3–40 letters (A–Z), digits, / or -; start with a letter or digit.')
        return serial

    def clean(self):
        cleaned = super().clean()
        student, register = cleaned.get('student'), cleaned.get('register')
        if student and register and register.student_id != student.pk:
            self.add_error('register', 'This course does not belong to the selected student.')
        if register and not self.instance.pk:
            if Certificate.objects.filter(
                register__student_id=register.student_id, register__course_id=register.course_id
            ).exists():
                self.add_error('register', 'A certificate has already been issued for this register. Edit it instead.')
        grade = cleaned.get('grade')
        if grade is not None and not (0 <= grade <= 100):
            self.add_error('grade', 'Grade must be between 0 and 100.')
        return cleaned


class SurveyQuestionForm(LocalizedModelForm):
    class Meta:
        model = SurveyQuestion
        fields = ('audience', 'title', 'position', 'active')
        widgets = {'title': forms.TextInput(attrs={'maxlength': 320, 'placeholder': _('Question wording')})}

    def clean_audience(self):
        audience = self.cleaned_data['audience']
        if self.instance.pk and self.instance.answers.exists() and audience != self.instance.audience:
            raise ValidationError(_('A question with saved answers cannot change its audience.'))
        return audience
