from functools import wraps

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from lms.models import Instructor


MANAGER_ROLE = 'Manager'
INSTRUCTOR_ROLE = 'Instructor'
ROLE_CHOICES = ((MANAGER_ROLE, _('Manager')), (INSTRUCTOR_ROLE, _('Instructor')))


def is_manager(user):
    return bool(user.is_authenticated and (user.is_superuser or
                user.groups.filter(name=MANAGER_ROLE).exists()))


def is_instructor(user):
    return bool(user.is_authenticated and not is_manager(user) and
                user.groups.filter(name=INSTRUCTOR_ROLE).exists())


def role_required(*allowed):
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)
            if ('manager' in allowed and is_manager(request.user)) or (
                    'instructor' in allowed and is_instructor(request.user)):
                return view(request, *args, **kwargs)
            raise PermissionDenied(_('This account does not have permission to access this page.'))
        return wrapped
    return decorator


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, label=_('First name'))
    last_name = forms.CharField(max_length=150, label=_('Last name'))
    email = forms.EmailField(label=_('Email address'))

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_('An account with this email already exists.'))
        return email


class AccountCreationForm(SignUpForm):
    role = forms.ChoiceField(choices=ROLE_CHOICES, label=_('Account role'))
    instructor = forms.ModelChoiceField(queryset=Instructor.objects.none(), required=False, label=_('Instructor profile'),
                                        empty_label=_('Choose an existing instructor'))

    def __init__(self, *args, instructor_only=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['instructor'].queryset = Instructor.objects.filter(user__isnull=True).order_by('last_name', 'first_name')
        if instructor_only:
            self.fields['role'].initial = INSTRUCTOR_ROLE
            self.fields['role'].widget = forms.HiddenInput()
        for field in self.fields.values():
            if not isinstance(field.widget, forms.HiddenInput):
                field.widget.attrs['class'] = 'form-control' if not isinstance(field.widget, forms.Select) else 'form-select'
                field.widget.attrs.setdefault('autocomplete', 'off')
        self.instructor_only = instructor_only
        self.order_fields(['first_name', 'last_name', 'username', 'email', 'role', 'instructor', 'password1', 'password2'])

    def clean(self):
        data = super().clean()
        if self.instructor_only and data.get('role') != INSTRUCTOR_ROLE:
            self.add_error('role', _('Invalid account role.'))
        if data.get('role') == INSTRUCTOR_ROLE and not data.get('instructor'):
            self.add_error('instructor', _('Choose the instructor profile for this account.'))
        if data.get('role') == MANAGER_ROLE and data.get('instructor'):
            self.add_error('instructor', _('Manager accounts are not linked to instructor profiles.'))
        return data


@transaction.atomic
def signup(request):
    if get_user_model().objects.exists():
        return render(request, 'registration/signup.html', {'bootstrap_closed': True})
    form = SignUpForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        # Concurrent first-account requests cannot create a public Manager after bootstrap.
        if get_user_model().objects.exists():
            raise PermissionDenied(_('Initial setup has already been completed.'))
        user = form.save()
        manager_group, _ = Group.objects.get_or_create(name=MANAGER_ROLE)
        user.groups.add(manager_group)
        login(request, user)
        return redirect('home')
    return render(request, 'registration/signup.html', {'form': form})


def _create_account(request, *, instructor_only):
    form = AccountCreationForm(request.POST or None, instructor_only=instructor_only)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            user = form.save()
            role, _ = Group.objects.get_or_create(name=form.cleaned_data['role'])
            user.groups.add(role)
            if form.cleaned_data['role'] == INSTRUCTOR_ROLE:
                instructor = form.cleaned_data['instructor']
                # Lock the profile to avoid linking it to two accounts.
                instructor = Instructor.objects.select_for_update().get(pk=instructor.pk, user__isnull=True)
                instructor.user = user
                instructor.save(update_fields=['user'])
        messages.success(request, _('The account was created successfully.'))
        return redirect('user_management')
    return render(request, 'registration/instructor_account.html', {
        'form': form, 'instructor_only': instructor_only,
    })


@role_required('manager')
def instructor_accounts(request):
    return _create_account(request, instructor_only=True)


@role_required('manager')
def create_account(request):
    return _create_account(request, instructor_only=False)


@role_required('manager')
def user_management(request):
    users = get_user_model().objects.prefetch_related('groups').select_related('instructor_profile').order_by('last_name', 'username')
    return render(request, 'registration/user_management.html', {
        'users': users,
        'unlinked_instructors': Instructor.objects.filter(user__isnull=True).order_by('last_name', 'first_name'),
    })


@role_required('manager')
def change_account_role(request, pk):
    if request.method != 'POST':
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(['POST'])
    if pk == request.user.pk:
        raise PermissionDenied(_('You cannot change your own role.'))
    target = get_object_or_404(get_user_model(), pk=pk, is_superuser=False)
    choice = request.POST.get('role')
    if choice not in (MANAGER_ROLE, INSTRUCTOR_ROLE):
        raise PermissionDenied(_('Invalid role.'))
    with transaction.atomic():
        profile = Instructor.objects.select_for_update().filter(user=target).first()
        if choice == INSTRUCTOR_ROLE and profile is None:
            profile_id = request.POST.get('instructor')
            if not profile_id or not profile_id.isdecimal():
                raise PermissionDenied(_('Choose the instructor profile for this account.'))
            profile = get_object_or_404(Instructor.objects.select_for_update().filter(user__isnull=True), pk=profile_id)
            profile.user = target
            profile.save(update_fields=['user'])
        elif choice == MANAGER_ROLE and profile is not None:
            profile.user = None
            profile.save(update_fields=['user'])
        groups = Group.objects.filter(name__in=(MANAGER_ROLE, INSTRUCTOR_ROLE))
        target.groups.remove(*groups)
        group, created = Group.objects.get_or_create(name=choice)
        target.groups.add(group)
    messages.success(request, _('Account role updated.'))
    return redirect('user_management')


def access_context(request):
    user = request.user
    return {
        'can_manage': is_manager(user),
        'is_instructor_role': is_instructor(user),
    }
