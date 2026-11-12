"""
URL configuration for congif project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts import views as account_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('lms.urls')),
    path('accounts/signup/', account_views.signup, name='signup'),
    path('accounts/instructors/new/', account_views.instructor_accounts, name='instructor_accounts'),
    path('accounts/users/', account_views.user_management, name='user_management'),
    path('accounts/users/new/', account_views.create_account, name='create_account'),
    path('accounts/users/<int:pk>/role/', account_views.change_account_role, name='change_account_role'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)