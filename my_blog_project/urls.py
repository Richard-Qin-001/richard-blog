"""
URL configuration for my_blog_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.contrib.auth import views as auth_views
from blog import views
from django.conf import settings
from django.conf.urls.static import static
from django_ratelimit.decorators import ratelimit

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', ratelimit(key='ip', rate='5/m', block=True)(auth_views.LoginView.as_view()), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('accounts/signup/', views.signup, name='signup'), 
    path('accounts/recovery/', views.password_recovery, name='password_recovery'),
    path('accounts/regenerate-key/', views.regenerate_key, name='regenerate_key'),
    path('captcha/', include('captcha.urls')),
    path('', include('blog.urls')),
    path('users/', views.user_list, name='user_list'),
    path('users/<str:username>/', views.profile_public, name='profile_public'),
    path('user/follow/', views.user_follow, name='user_follow'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
