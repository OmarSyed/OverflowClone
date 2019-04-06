from django.urls import path
from . import views

urlpatterns = [
    path('adduser', views.add_user, name='adduser'),
    path('login', views.log_in, name='login'),
    path('logout', views.log_out, name='logout'),
    path('verify', views.verify,name='verify'),
    path('questions/add', views.add_question, name='add_question'),
    path('questions/<title>', views.get_question, name='exact_post'),
    path('questions/<title>/answers/add', views.add_comment, name='add_comment'),
    path('questions/<title>/answers', views.get_comments, name='get_comments'),
    path('search', views.search, name='search'),
    
]
