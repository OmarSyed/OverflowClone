from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from .models import Account, Post, Comment, Tag, ViewerAccounts, ViewerIP, QuestionUpvotes, QuestionDownvotes, CommentUpvotes, CommentDownvotes
import json
import operator
from functools import reduce
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
            #print(json_data) 
            title = json_data['title'] 
            if len(title) > 255:
                title = title[:255]
                print(title)
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
            #print(data) 
            return JsonResponse(data)
        except Exception as e:
            print(e)
            data = {'status': 'error', 'error':'Error posting question'}
            print(data)
            return JsonResponse(data)
    else:
        data = {'status': 'error', 'error': 'You are not logged in'}
        print(data) 
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
                    added_tag = tag.tag
                    tags.append(added_tag)
                accepted_answer = Comment.objects.filter(post = question, accepted = True)
                answer_id = None
                if not accepted_answer:
                    answer_id = 'Null'
                else:
                    answer_id = accepted_answer.comment_id
                id_ = question.slug
                title = question.title
                body = question.body 
                data = {}
                data['status'] = 'OK'
                data['question'] = {'id': id_, 'user':{'username':question.poster.username, 'reputation':question.poster.reputation},'title':title, 'body': body, 'score':question.score, 'view_count':question.views, 'answer_count': question.answer_count, 'timestamp': question.time_added, 'media':[], 'tags':tags, 'accepted_answer_id':answer_id}
                data['error'] = ''
                print(data) 
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
                    #print(tag.tag)
                    tags.append(tag.tag)
                accepted_answer = Comment.objects.filter(post = question, accepted = True)
                answer_id = None
                if not accepted_answer:
                    answer_id = 'Null'
                else:
                    answer_id = accepted_answer.comment_id
                print(question.slug)
                print(question.title)
                print(question.body) 
                data = {}
                data['status'] = 'OK'
                data['question'] = {'id': question.slug, 'user':{'username':'', 'reputation':''},'title': question.title, 'score':question.score, 'body': question.body, 'view_count':question.views, 'answer_count': question.answer_count, 'timestamp': question.time_added, 'media':[], 'tags':tags, 'accepted_answer_id':answer_id}
                data['error'] = ''
                return JsonResponse(data)
        except Exception as e:
            print(e)
            data = {'status':'error', 'error':'Unable to retrive specified question'}
            return JsonResponse(data)
    # Delete question if the question's poster is logged in 
    elif request.method == 'DELETE':
        try:
            if 'username' in request.session:
                account = Account.objects.get(username=request.session['username']) 
                is_deleted = Post.objects.filter(slug=title, poster=account)
                if is_deleted:
                    print("success")
                    is_deleted.delete() 
                    return HttpResponse(status=200) 
                else:
                    print('incorrect account') 
                    return HttpResponse(status=403)
            else:
                print('not logged in') 
                return HttpResponse(status=401) 
        except Exception as e:
            print(e)  
            return HttpResponseBadRequest 

@csrf_exempt
def up_or_downvote_question(request, title):
    # default upvote is true
    upvote = True
    if request.method == 'POST':
        if 'username' in request.session:
            user = Accounts.objects.get(username = request.session['username'])
            question = Post.objects.get(slug = title) 
            json_data = json.loads(request.body) 
            upvote = json_data['upvote'] 
            found_upvote = QuestionUpvotes.objects.filter(upvoter = user, question = question) 
            found_downvote = QuestionDownvotes.objects.filter(downvoter = user, question = question) 
            if found_upvote:
                # if upvote already exists in database, then undo the upvote
                question.score -= 1
                found_upvote.delete()
                # if upvote parameter is false, then subtract 1 from upvote count and add a new downvote to database
                if not upvote: 
                    question.score -= 1 
                    QuestionDownvotes.objects.create(downvoter = user, question = question) # Create a new downvote in the system
                question.save() 
            elif found_downvote:
                # if a downvote from this user already exists, then undo the downvote
                question.score += 1
                found_downvote.delete() 
                # if the upvote parameter is true, then add 1 to upvote count and add a new upvote to the database 
                if upvote:
                    question.score += 1
                    QuestionUpvotes.objects.create(upvoter = user, question = question) 
                question.save() 
            else: 
                 # if no instances of an upvote/downvote for this question by this user was found, add upvote/downvote to table and make adjustments to question's score based on value of upvote
                if upvote: 
                    question.score += 1
                    question.save() 
                    QuestionUpvotes.objects.create(upvoter=user, question=question) 
                else:
                    question.score -= 1
                    question.save() 
                    QuestionDownvotes.objects.create(downvoter=user, question=question) 
                data = {'status' : 'OK'} 
                return JsonResponse(data) 
        else:
            data = {'status' : 'error'} 
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
def up_or_downvote_answer(request, url):
    data = {} 
    if request.method == 'POST':
        if 'username' in request.session:
            try:
                json_data = json.loads(request.body)
                comment = Comment.objects.get(comment_url=url)
                user = Account.objects.get(username=request.session['username']) 
                upvote = json_data['upvote']
                found_upvote = CommentUpvotes.objects.filter(answer=comment, upvoter=user) 
                found_downvote = CommentDownvotes.objects.filter(answer=comment, downvoter=user) 
                if found_upvote:
                    comment.score -= 1 
                    found_upvote.delete() 
                    if not upvote:
                        comment.score -= 1
                        CommentDownvotes.objects.create(answer=comment, downvoter=user) 
                    comment.save() 
                elif found_downvote:
                    comment.score += 1
                    found_downvote.delete() 
                    if upvote:
                        comment.score += 1
                        CommentUpvotes.objects.create(answer=comment, upvoter=user) 
                    comment.save() 
                else: 
                    if upvote:
                        CommentUpvotes.objects.create(answer=comment, upvoter=user) 
                        comment.score += 1 
                        comment.save() 
                    else:
                        CommentDownvotes.objects.create(answer=comment, downvoter=user) 
                        comment.score -= 1
                        comment.save()
                data['status'] = 'OK'
                return JsonResponse(data) 
            except Exception as e:
                print(e) 
                data['status'] = 'error'
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
        # Default search query
        search_query = '' 
        json_data = json.loads(request.body)
        #print(json_data) 
        # If timestamp is in json request, then set timestamp to that
        if 'timestamp' in json_data:
            timestamp = math.floor(json_data['timestamp'])
        if 'limit' in json_data:
            # If limit is in json data and is less than 100, then set limit to that
            if json_data['limit'] > 100:
                limit = 100
            else:
                limit = json_data['limit']
        if 'q' in json_data:
            search_query = json_data['q']
        data = {}
        data['status'] = 'OK'
        data['questions'] = []
        # Keep track of how many question you return
        i = 0
        # Retrieve all questions which were added at or before the timestamp, depending on search query
        questions = None
        if search_query == '':
            questions = Post.objects.filter(time_added__lte=timestamp)
        else:
            q_list = [Q(body__icontains=' '+search_query+' '), Q(title__icontains=' '+search_query+' ') ]
            words = search_query.split(' ') 
            if len(words) > 1:
                for word in words:
                    q_list.extend([Q(body__icontains=' '+word+' '), Q(title__icontains=' '+word+' ')])
            questions = Post.objects.filter(reduce(operator.or_, q_list), time_added__lte=timestamp)
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
            data['questions'].append({'id':question.slug, 'user': {'username':question.poster.username, 'reputation':question.poster.reputation}, 'title':question.title, 'body':question.body, 'score':question.score, 'view_count':question.views, 'answer_count':question.answer_count, 'timestamp':question.time_added, 'media': [], 'tags': tags, 'accepted_answer_id':accepted_answer_id})
            i += 1
        data['error'] = ''
        #for a in data['questions']:
        #   print(a) 
        return JsonResponse(data)
    except Exception as e:
        print(e)
        data = {'status':'error', 'questions':[], 'error':'Trouble with your query'}
        return JsonResponse(data)           
