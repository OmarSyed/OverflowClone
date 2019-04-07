from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Account, Post, Comment, Tag, ViewerAccounts, ViewerIP
import json
from random import choice
from string import ascii_uppercase
import math
import datetime

@csrf_exempt
def add_question(request):
    if 'username' in request.session:
        try:
            # Get the appropriate data from json POST request form
            json_data = json.loads(request.body)
            title = json_data['title']
            body = json_data['body']
            tags = json_data['tags']
            # Get the account associated with the current user's session
            account = Account.objects.get(username=request.session['username'])
            timeadded = math.floor(datetime.datetime.utcnow().timestamp() - 14400)
            # Add a new question to the database with user account associated with the question
            new_post = Post(poster=account, title=title, body=body, time_added=timeadded)
            new_post.save()
            i = 1
            for tag in tags:
                new_tag =  Tag(associated_post=new_post, tag=tag)
                new_tag.save()
            data = {'status': 'OK','id':new_post.slug, 'error': ''}
            return JsonResponse(data)
        except Exception as e:
            data = {'status': 'error', 'error':'Error posting question'}
            return JsonResponse(data)
    else:
        data = {'status': 'error', 'error': 'You are not logged in'}
        return JsonResponse(data)

@csrf_exempt
def get_question(request, title):
    if request.method == 'GET':
        try:
            # Check whether the user is currently logged in or not. If not, they will be treated as a guest and identified by IP
            if 'username' in request.session:
                tags = []
                question = Post.objects.get(slug = title)
                username = request.session['username']
                # Retrieve account associated with logged in user from the database
                account = Account.objects.get(username=username)
                # If the account has not viewed the current question, then increment the question's view count and add the account to the table of Viewer Accounts
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
                return JsonResponse(data)
            else:
                tags = []
                # Get the current user's IP address
                ip_address = request.META['REMOTE_ADDR']
                question = Post.objects.get(slug = title)
                account = question.poster
                # Check if the IP address is associated with this question in the database
                if not ViewerIP.objects.filter(ip_address = ip_address, post = question):
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
                return JsonResponse(data)
        except Exception as e:
            print(e)
            data = {'status':'error', 'error':'Unable to retrive specified question'}
            return JsonResponse(data) 

@csrf_exempt
def add_comment(request, title):
    # Check whether user is currently logged in 
    if 'username' in request.session:
        try:
            json_data = json.loads(request.body) 
            body = json_data['body'] 
            # Get the question associated with the title in the url 
            question = Post.objects.get(slug=title)
            question.answer_count += 1
            question.save()  
            # Get the account associated with the current user
            account = Account.objects.get(username=request.session['username'])
            comment_url = ''.join(choice(ascii_uppercase) for i in range(12))
            timestamp = math.floor(datetime.datetime.utcnow().timestamp() - 14400)
            # Add the user's comment to the database
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
        # Get the question corresponding to the title in URL
        question = Post.objects.get(slug=title)
        data = {}
        data['answers'] = []
        # Get all comments associated with the question
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
        # Default limit for number of returned questions
        limit = 25
        json_data = json.loads(request.body)
        # If timestamp is in json request, then set timestamp to that
        if 'timestamp' in json_data:
            timestamp = math.floor(json_data['timestamp'])
        if 'limit' in json_data:
            # If limit is in json data and is less than 100, then set limit to that
            if json_data['limit'] > 100:
                limit = 100
            else:
                limit = json_data['limit']
        data = {}
        data['status'] = 'OK'
        data['questions'] = []
        # Keep track of how many question you return
        i = 0
        # Retrieve all questions which were added at or before the timestamp
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
        return JsonResponse(data)
    except Exception as e:
        print(e)
        data = {'status':'error', 'questions':[], 'error':'Trouble with your query'}
        return JsonResponse(data)           
