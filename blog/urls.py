from django.urls import path
from . import views

urlpatterns = [
    path('', views.post_list, name='post_list'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('post/new/', views.post_new, name='post_new'),
    path('post/<int:pk>/edit/', views.post_edit, name='post_edit'),
    path('post/<int:pk>/remove/', views.post_remove, name='post_remove'),
    path('comment/<int:pk>/edit/', views.comment_edit, name='comment_edit'),
    path('comment/<int:pk>/remove/', views.comment_remove, name='comment_remove'),
    path('post/<int:pk>/like/', views.post_like, name='post_like'),
    path('comment/<int:pk>/like/', views.comment_like, name='comment_like'),
    path('tag/<str:tag_name>/', views.post_list, name='post_list_by_tag'),
    path('tag/<int:pk>/delete/', views.tag_delete, name='tag_delete'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('attachment/<int:pk>/delete/', views.attachment_delete, name='attachment_delete'),
    path('api/image/upload/', views.api_image_upload, name='api_image_upload'),
]