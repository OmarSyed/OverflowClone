
import json
from django.core.mail import send_mail
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.forms import Form
from .forms import SignUpForm, VerificationForm, LogInForm
from django.utils.crypto import get_random_string
from .credentials import email_user, email_pass
from .models import Account, Post, Comment
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout

def check_if_account_exists(user_name, emailaddr):
    if Account.objects.filter(username=user_name) or Account.objects.filter(email= emailaddr):
        return True
    return False

def default(request):
    logged_in = False
    if request.user.is_authenticated:
        logged_in = True 
    return render(request, "home.html", {'logged_in':logged_in})

def add_user(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST) 
        if form.is_valid():
            user = form.save() 
            user.is_active = False
            verification_id = get_random_string(length=12) 
            email = form.cleaned_data.get('email') 
            send_mail('Your verification code', 'Your verification code is '+verification_id+'; please enter this code at /verify',from_email='johnsmith5427689@gmail.com',recipient_list=[email])
            Account.objects.create(account=user, verification_id = verification_id) 
            return render(request, "verified.html", {'email':email, 'logged_in':False}) 
        else:
            logged_in = False
            form = SignUpForm()
    else:
        form = SignUpForm()
        logged_in = False
        if request.user.is_authenticated:
            print('User is signed in') 
            logged_in = True
            form = None
            return render(request, 'signup.html', {'form': form, 'logged_in':logged_in})
    return render(request, 'signup.html', {'form':form, 'logged_in':logged_in})


def verify(request):
    if request.method == 'POST':
        logged_in = False 
        if request.user.is_authenticated:
            logged_in = True 
        form = VerificationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            verification_key = form.cleaned_data['key']
            found_account = Account.objects.filter(verification_id = verification_key) 
            if found_account: 
                found_account[0].account.is_active = True 
                username = found_account[0].account.username
                return render(request, 'verify_success.html', {'email':email, 'username':username, 'logged_in':logged_in}) 
            else:
                print('enter valid email or verification key') 
                form = VerificationForm()
        else:
            form = VerificationForm() 
    else:
        logged_in = False 
        if request.user.is_authenticated:
            logged_in = True
        form = VerificationForm() 
    return render(request, 'verify.html', {'form':form, 'logged_in':logged_in}) 

def log_in(request):
    if request.method == 'POST':
        logged_in = False
        # Check first whether the username is already logged in
        if request.user.is_authenticated: 
            msg = 'You are already logged in'
            logged_in = True
            return render(request, 'signin.html', {'logged_in':logged_in, 'msg':msg})
        form = LogInForm(request.POST)  
        username = request.POST['username'] 
        password = request.POST['password'] 
        user = authenticate(username=username, password=password) 
        if user is not None: 
            login(request, user) 
            return render(request, 'home.html', {'logged_in':True})
        else:
            return render(request, 'signin.html', {'logged_in':False, 'msg':'Incorrect username or password'})
    else:
        logged_in = False
        if request.user.is_authenticated:
            logged_in = True
            return render(request, 'signin.html', {'logged_in':logged_in, 'msg':'You are logged in already'})
        form = LogInForm() 
        return render(request, 'signin.html', {'logged_in': logged_in, 'form':form}) 

@login_required
def log_out(request):
    logout(request)
    logged_in = False
    #print('username : '+request.user.username) 
    return render(request, 'home.html', {'logged_in':False})  


@csrf_exempt
def get_user(request, username):
    if request.method == 'GET':
        try:
            account = Account.objects.get(username=username)
            data = {} 
            data['status'] = 'OK'
            data['user'] = {'email':account.email, 'reputation':account.reputation}
            return JsonResponse(data) 
        except:
            data = {} 
            data['status'] = 'error'
            data['user'] = {'email':'', 'reputation': 'Null'} 
            return JsonResponse(data, status=401) 

@csrf_exempt
def get_user_questions(request, username):
    data = {} 
    data['questions'] = [] 
    if request.method == 'GET':
        try:
            account = Account.objects.get(username=username) 
            all_questions = Post.objects.filter(poster=account) 
            if all_questions:
                for question in all_questions:
                    data['questions'].append(question.slug)
            data['status'] = 'OK'
            return JsonResponse(data) 
        except Exception as e:
            print(e) 
            data['status'] = 'error'
            return JsonResponse(data, status=401) 

@csrf_exempt
def get_user_answers(request, username): 
    data = {}
    data['answers'] = [] 
    if request.method == 'GET':
        try:
            account = Account.objects.get(username=username) 
            all_answers = Comment.objects.filter(poster=account) 
            if all_answers:
                for answer in all_answers:
                    data['answers'].append(answer.comment_url) 
            data['status'] = 'OK'
            return JsonResponse(data) 
        except Exception as e:
            print(e) 
            data['status'] = 'error'
            return JsonResponse(data, status=401) 
