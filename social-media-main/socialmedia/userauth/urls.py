from django.contrib import admin
from django.urls import path
from socialmedia import settings
from userauth import views
from django.conf.urls.static import static

urlpatterns = [
    path('',views.home),
    path('loginn/',views.loginn),
    path('signup/',views.signup),
    path('logoutt/',views.logoutt),
    path('upload',views.upload),
    path('upload-story/', views.upload_story, name='upload_story'),
    path('like-post/<str:id>', views.likes, name='like-post'),
    path('comment/<str:id>/', views.add_comment, name='add_comment'),
    path('messages/', views.messages, name='messages'),
    path('send-message/', views.send_message, name='send_message'),
    path('#<str:id>', views.home_post),
    path('explore',views.explore),
    path('profile/<str:id_user>', views.profile),
    path('delete/<str:id>', views.delete),
    path('delete-story/<str:id>/', views.delete_story, name='delete_story'),
    path('delete-message/<str:id>/', views.delete_message, name='delete_message'),
    path('search-results/', views.search_results, name='search_results'),
    path('follow', views.follow, name='follow'),
]
