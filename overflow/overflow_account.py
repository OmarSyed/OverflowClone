from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from .models import Account, Post, Comment, Tag, ViewerAccounts, ViewerIP
import json
from random import choice
from string import ascii_uppercase
import math  
import datetime

def check_if_account_exists(user_name, emailaddr):
    if Account.objects.filter(username=user_name) or Account.objects.filter(email= emailaddr):
        return True
    return False

@csrf_exempt
def add_user(request):
    if request.method == 'POST':
        # Get the appropriate json request data
        json_data = json.loads(request.body)
        username = json_data['username']
        password = json_data['password']
        email = json_data['email']
        try:
            # Create random key 
            random_key = ''.join(choice(ascii_uppercase) for i in range(12)) 
            # Check to see if account with the same username or email already exists
            if check_if_account_exists(username, email):
                data = {'status' :'error', 'error': 'Account already exists'}
                return JsonResponse(data)
            new_account = Account.objects.create(username=username, password=password, email=email,verification_key=random_key)
            data = {'status': 'OK', 'error':''}
            message = 'validation key: <' + random_key + '>'
            # send a verification email out to the email of the new user
            sent_message = send_mail('Verification key', message, 'johnsmith5427689@gmail.com', [email], fail_silently=False)
            if sent_message == 0:
                data['status'] = 'error'
                data['error'] = 'Error sending out email'
                return JsonResponse(data)
            return JsonResponse(data)
        except Exception as e:
            print(e)
            response_data = {'status': 'error', 'error': 'Unable to create account'}
            return JsonResponse(response_data)

@csrf_exempt
def verify(request):
    # Get the appropriate json data 
    json_data = json.loads(request.body)
    email = json_data['email']
    key = json_data['key']
    try:
        # Retrieve the account with the corresponding email and set verified field = true
        account = Account.objects.get(email=email, verification_key=key)
        account.verified = True
        account.save()
        data = {'status':'OK', 'error':''}
        return JsonResponse(data)
    except:
        data = {'status':'error', 'error': 'Could not verify backdoor key'}
        return JsonResponse(data)

@csrf_exempt
def log_in(request):
    if request.method == 'POST':
        # Check first whether the username is already logged in 
        if 'username' in request.session:
            data = {'status':'error', 'error': 'You are logged in already'}
            return JsonResponse(data) 
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
                return JsonResponse(response_data)
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
            return JsonResponse(data)
