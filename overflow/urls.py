from django.urls import path
from . import overflow_account
from . import questions

urlpatterns = [
    path('adduser', overflow_account.add_user, name='adduser'),
    path('login', overflow_account.log_in, name='login'),
    path('logout', overflow_account.log_out, name='logout'),
    path('verify', overflow_account.verify, name='verify'),
    path('questions/add', views.add_question, name='add_question'),
    path('questions/<title>', views.get_question, name='exact_post'),
    path('questions/<title>/answers/add', views.add_comment, name='add_comment'),
    path('questions/<title>/answers', views.get_comments, name='get_comments'),
    path('search', views.search, name='search'),
    
]
