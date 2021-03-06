from django.urls import path
from . import overflow_account, questions, media

urlpatterns = [
    path('', overflow_account.default, name='default'),
    path('adduser', overflow_account.add_user, name='adduser'),
    path('login', overflow_account.log_in, name='login'),
    path('logout', overflow_account.log_out, name='logout'),
    path('verify', overflow_account.verify, name='verify'),
    path('questions/add', questions.add_question, name='add_question'),
    path('questions/<title>', questions.get_question, name='exact_post'),
    path('questions/<title>/upvote', questions.up_or_downvote_question, name='up_or_downvote_question'), 
    path('questions/<title>/answers/add', questions.add_comment, name='add_comment'),
    path('questions/<title>/answers', questions.get_comments, name='get_comments'),
    path('answers/<url>/upvote', questions.up_or_downvote_answer, name='up_or_downvote_comment'),
    path('answers/<url>/accept', questions.accept_comment, name='accept_answer'),
    path('user/<username>', overflow_account.get_user, name='get_user'),
    path('user/<username>/questions', overflow_account.get_user_questions, name='get_user_questions'),
    path('user/<username>/answers', overflow_account.get_user_answers, name='get_user_answers'),
    path('search', questions.search, name='search'),
    path('addmedia', media.addMedia, name = 'add_media'),
    path('media/<media_id>', media.getMedia, name='get_media'), 
    
]
