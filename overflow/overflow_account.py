
import json
from django.core.mail import send_mail
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .forms import SignUpForm
from django.utils.crypto import get_random_string
from .credentials import email_user, email_pass
from .models import Account, Post, Comment

def check_if_account_exists(user_name, emailaddr):
    if Account.objects.filter(username=user_name) or Account.objects.filter(email= emailaddr):
        return True
    return False

def default(request):
    return HttpResponse("Hello, welcome to the front page")

def add_user(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST) 
        if form.is_valid():
            user = form.save() 
            user.is_active = False
            verification_id = get_random_string(length=12) 
            email = form.cleaned_data.get('email') 
            send_mail('Your verification code', 'Your verification code is '+verification_id+'; please enter this code at /verify',from_email='johnsmith5427689@gmail.com',recipient_list=[email])
            print('line 29') 
            Account.objects.create(account=user, verification_id = verification_id) 
            return render(request, "verified.html", {'email':email}) 
        else:
            form = SignUpForm()
    else:
        form = SignUpForm() 
    return render(request, 'login.html', {'form':form})

@csrf_exempt
def verify(request):
    # Get the appropriate json data 
    json_data = json.loads(request.body)
    email = json_data['email']
    key = json_data['key']
    print(json_data)
    try:
        # Retrieve the account with the corresponding email and set verified field = true
        account = Account.objects.get(email=email, verification_key=key)
        account.verified = True
        account.save()
        data = {'status':'OK', 'error':''}
        return JsonResponse(data)
    except:
        data = {'status':'error', 'error': 'Could not verify backdoor key'}
        return JsonResponse(data, status=401)

@csrf_exempt
def log_in(request):
    if request.method == 'POST':
        # Check first whether the username is already logged in 
        if 'username' in request.session:
            data = {'status':'error', 'error': 'You are logged in already'}
            return JsonResponse(data, status=401) 
        # Retrieve appropriate json data 
        json_data = json.loads(request.body)
        username = json_data['username']
        password = json_data['password']
        try:
            # Retrieve the account with the associated email 
            account = Account.objects.get(username=username, password=password)
            # If account is not verified then return error response
            if not account.verified: 
                response_data = {'status': 'error', 'error' : 'Account is not verified, please check email and verify account.'}
                return JsonResponse(response_data, status=401)
            else:
                request.session['username'] = username
                response_data = {'status' : 'OK', 'error': ''}
                return JsonResponse(response_data)
        except:
            response_data = {'status': 'error', 'error' : 'Account does not exist'}
            return JsonResponse(response_data)

@csrf_exempt
def log_out(request):
    if request.method == 'POST':
        # Delete the username from request.session to end session 
        try:
            del request.session['username']
            data = {'status': 'OK', 'error': ''}
            return JsonResponse(data)
        except:
            data = {'status': 'error', 'error': 'You are logged out already. '}
            return JsonResponse(data, status=401)

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
