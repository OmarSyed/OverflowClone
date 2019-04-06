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

# Create your views here.
@csrf_exempt
def add_user(request):
    if request.method == 'POST':
        json_data = json.loads(request.body)
        username = json_data['username']
        password = json_data['password']
        email = json_data['email']
        try:
            random_key = ''.join(choice(ascii_uppercase) for i in range(12)) 
            if check_if_account_exists(username, email):
                data = {'status' :'error', 'error': 'Account already exists'}
                return JsonResponse(data)
            new_account = Account.objects.create(username=username, password=password, email=email,verification_key=random_key)
            data = {'status': 'OK', 'error':''}
            message = 'validation key: <' + random_key + '>'
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
    json_data = json.loads(request.body)
    email = json_data['email']
    key = json_data['key']
    try:
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
        if 'username' in request.session:
            data = {'status':'error', 'error': 'You are logged in already'}
            return JsonResponse(data) 
        json_data = json.loads(request.body)
        username = json_data['username']
        password = json_data['password']
        try:
            account = Account.objects.get(username=username, password=password)
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
        try:
            del request.session['username']
            data = {'status': 'OK', 'error': ''}
            return JsonResponse(data)
        except:
            data = {'status': 'error', 'error': 'You are logged out already. '}
            return JsonResponse(data)

@csrf_exempt 
def add_question(request):
    if 'username' in request.session:
        try:
            json_data = json.loads(request.body)  
            title = json_data['title'] 
            body = json_data['body'] 
            tags = json_data['tags'] 
      #      print('title: '+ title)
     #       print('body: '+ body)
            account = Account.objects.get(username=request.session['username'])
            timeadded = math.floor(datetime.datetime.utcnow().timestamp() - 14400) 
            new_post = Post(poster=account, title=title, body=body, time_added=timeadded)
            new_post.save() 
            i = 1
            for tag in tags:
    #            print('tag ' + str(i) + ': ' + tag) 
                new_tag =  Tag(associated_post=new_post, tag=tag)
                new_tag.save()
            #new_view = ViewerAccounts(viewer=account, post=new_post)
            #new_view.save() 
            data = {'status': 'OK','id':new_post.slug, 'error': ''}
            #print(title + ' added at ' + str(timeadded)) 
   #         print(data)
  #          print('user: ' + request.session['username']) 
            return JsonResponse(data) 
        except Exception as e:
            print(e) 
            data = {'status': 'error', 'error':'Error posting question'}
 #           print(data)
            return JsonResponse(data) 
    else:
        data = {'status': 'error', 'error': 'You are not logged in'}
#        print(data)
        return JsonResponse(data) 

@csrf_exempt
def get_question(request, title):
    if request.method == 'GET':
        try:
            if 'username' in request.session:
                tags = []
                question = Post.objects.get(slug = title)
                username = request.session['username']
                account = Account.objects.get(username=username)
                if not ViewerAccounts.objects.filter(viewer=account, post=question): 
                    question.views += 1
                    question.save() 
                    new_viewer = ViewerAccounts(viewer = account, post = question)
                    new_viewer.save()
                tag_set = Tag.objects.filter(associated_post = question) 
                for tag in tag_set:
                    tags.append(tag.tag)
                accepted_answer = Comment.objects.filter(post = question, accepted = True)
                answer_id = None
                if not accepted_answer:
                    answer_id = 'Null'
                else:
                    answer_id = accepted_answer.comment_id 
                data = {}
                data['status'] = 'OK'
                data['question'] = {'id': question.slug, 'user':{'username':question.poster.username, 'reputation':question.poster.reputation},'title':question.title, 'body': question.body, 'score':question.score, 'view_count':question.views, 'answer_count': question.answer_count, 'timestamp': question.time_added, 'media':[], 'tags':tags, 'accepted_answer_id':answer_id}
                data['error'] = ''
                #print(data) 
                return JsonResponse(data)
            else:
                tags = []
                #username = account.username 
                #reputation = account.reputation 
                ip_address = request.META['REMOTE_ADDR']
               # print(ip_address) 
                question = Post.objects.get(slug = title)
                account = question.poster
                if not ViewerIP.objects.filter(ip_address = ip_address, post = question):
                #    print('IP did not view this question before') 
                    question.views += 1
                    question.save()
                    new_viewer = ViewerIP(ip_address = ip_address, post = question)
                    new_viewer.save()
                    viewer_set = ViewerIP.objects.filter(post=question)
                tag_set = Tag.objects.filter(associated_post = question)
                for tag in tag_set:
                    tags.append(tag.tag)
                accepted_answer = Comment.objects.filter(post = question, accepted = True)
                answer_id = None
                if not accepted_answer:
                    answer_id = 'Null'
                else:
                    answer_id = accepted_answer.comment_id
                data = {}
                data['status'] = 'OK'
                data['question'] = {'id': question.slug, 'user':{'username':'', 'reputation':''},'title':question.title, 'score':question.score, 'body': question.body, 'view_count':question.views, 'answer_count': question.answer_count, 'timestamp': question.time_added, 'media':[], 'tags':tags, 'accepted_answer_id':answer_id}
                data['error'] = ''
              #  print(data) 
                return JsonResponse(data)
        except Exception as e:
            print(e)
            data = {'status':'error', 'error':'Unable to retrive specified question'}
            return JsonResponse(data) 

@csrf_exempt
def add_comment(request, title):
    if 'username' in request.session:
        try:
            json_data = json.loads(request.body) 
            body = json_data['body'] 
            question = Post.objects.get(slug=title)
            #print('Initial question ' + question.title + 'answer count: ' + str(question.answer_count)) 
            question.answer_count += 1
            question.save() 
            #print('Post question ' + question.title + 'answer count: ' + str(question.answer_count)) 
            account = Account.objects.get(username=request.session['username'])
            comment_url = ''.join(choice(ascii_uppercase) for i in range(12))
            timestamp = math.floor(datetime.datetime.utcnow().timestamp() - 14400)
            new_comment = Comment.objects.create(comment_url=comment_url, poster=account, post=question, comment=body, time_posted=timestamp)
            data = {'status':'OK', 'id':comment_url, 'error':''} 
            return JsonResponse(data) 
        except Exception as e:
            print(e) 
            data = {'status':'error', 'id':'', 'error':'Error retrieving question'}
            return JsonResponse(data) 
    else:
        data = {'status' :'error', 'error':'You are not logged in'}
        return JsonResponse(data)

@csrf_exempt
def get_comments(request, title):
    try:
        question = Post.objects.get(slug=title) 
        data = {} 
        data['answers'] = []
        all_comments = Comment.objects.filter(post=question) 
        for comment in all_comments:
            data['answers'].append({'id': comment.comment_url, 'user':comment.poster.username, 'body':comment.comment, 'score':comment.score, 'is_accepted':comment.accepted, 'timestamp':comment.time_posted, 'media':[]}) 
        data['status'] = 'OK'
        data['error'] = ''
        return JsonResponse(data) 
    except Exception as e:
        print(e) 
        data = {'answers': [], 'status':'error', 'error':'error getting comments for question'}
        return JsonResponse(data) 

@csrf_exempt
def search(request):
    try:
        timestamp = math.floor(datetime.datetime.utcnow().timestamp() - 14400) 
        limit = 25
        print(request.body) 
        json_data = json.loads(request.body)
        if 'timestamp' in json_data:
            #if math.floor(json_data['timestamp']) <= timestamp:
                #print('timestamp that was sent is less than current time')
            timestamp = math.floor(json_data['timestamp'])
        if 'limit' in json_data:
            if json_data['limit'] > 100:
                limit = 100
            else:
                limit = json_data['limit'] 
        data = {} 
        data['status'] = 'OK'
        data['questions'] = []
        i = 0 
        questions = Post.objects.filter(time_added__lte=timestamp) 
        for question in questions:
            if i >= limit:
                break
            associated_tags = Tag.objects.filter(associated_post = question) 
            tags = []
            for tag in associated_tags:
                tags.append(tag.tag)
            associated_comments = Comment.objects.filter(post = question, accepted = True)
            accepted_answer_id = None
            if associated_comments:
                accepted_answer_id = associated_comments.comment_url
            else:
                accepted_answer_id = 'Null'
            data['questions'].append({'id':question.slug, 'user': {'username':question.poster.username, 'reputation':question.poster.reputation}, 'title':question.title, 'body':question.body, 'score':question.score, 'view_count':question.views, 'answer_count':question.answer_count, 'timestamp':question.time_added, 'media':[], 'tags': tags, 'accepted_answer_id':accepted_answer_id})
            i += 1
        data['error'] = ''
        print(data) 
        return JsonResponse(data)
    except Exception as e:
        print(e)
        data = {'status':'error', 'questions':[], 'error':'Trouble with your query'}
        print(data) 
        return JsonResponse(data)
