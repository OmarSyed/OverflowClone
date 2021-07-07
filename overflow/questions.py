from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User
from .models import Account, Post, Comment, Tag, ViewerAccounts, ViewerIP, QuestionUpvotes, QuestionDownvotes, CommentUpvotes, CommentDownvotes, Media, QuestionMedia, CommentMedia
from .forms import QuestionForm, TagsForm
import json
import operator
from functools import reduce
from random import choice
from string import ascii_uppercase
import math
import datetime

def create_search_query(tags, has_media, accepted, query, sort_by, timestamp):
    sql_statement = "SELECT * FROM overflow_post WHERE time_added <= '"+str(timestamp)+"'"
    if len(tags) > 1:
        sql_statement += ' AND post_id IN (SELECT T1.associated_post_id FROM '
        num_tags = 1
        # Creating the necessary tables in the subquery
        while num_tags <= len(tags):
            if num_tags == len(tags):
                sql_statement += 'overflow_tag T'+str(num_tags)
            else:
                sql_statement += 'overflow_tag T'+str(num_tags)+', '
            num_tags += 1
        num_tags = 2
        # Creating the conditions for the subquery
        sql_statement += ' WHERE '
        # getting the rows with the same question_id
        while num_tags <= len(tags):
            sql_statement += 'T1.associated_post_id = T'+str(num_tags)+'.associated_post_id AND '
            num_tags += 1
        num_tags = 1
        while num_tags <= len(tags):
            if num_tags == len(tags):
                sql_statement += "T"+str(num_tags)+".tag = '"+tags[num_tags-1]+"') "
            else:
                sql_statement += "T"+str(num_tags)+".tag = '"+tags[num_tags-1]+"' AND "
            num_tags += 1
        if has_media:
            sql_statement += ' AND has_media = 1 '
        if accepted:
            sql_statement += ' AND solved = 1 '
    elif len(tags) == 1:
        sql_statement += ' AND post_id IN (SELECT T1.associated_post_id FROM '
        sql_statement += "overflow_tag T1 WHERE T1.tag = '" + tags[0] + "')"
        if has_media:
            sql_statement += ' AND has_media = 1'
        if accepted:
            sql_statement += ' AND solved = 1 '
    else:
        if has_media:
            sql_statement += ' AND has_media = 1 '
        if accepted: 
            sql_statement += ' AND solved = 1 ' 
    if query != '': 
        sql_statement += " AND MATCH (title,body) AGAINST ('"+ query + "' IN BOOLEAN MODE)" 
    if sort_by == 'timestamp':
       sql_statement += ' ORDER BY time_added DESC;' 
    else:
        sql_statement += ' ORDER BY score DESC;'
    #print (sql_statement) 
    return sql_statement

def add_question(request):
    new_post = None
    if request.method == 'POST':
        if request.user.is_authenticated:
            form = QuestionForm(request.POST)
            form2 = TagsForm(request.POST) 
            if form.is_valid():
                poster = User.objects.get(username=request.user.username) # get the User object first because it is a foreignkey
                title = form.cleaned_data['title']
                body = form.cleaned_data['body'] 
                url = slugify(title) 
                current_time = datetime.datetime.now() 
            if form2.is_valid():
                tags = form2.cleaned_data['tag'].strip().split(',')
                new_post = Post.objects.create(poster=poster, title=title, body=body, slug=url, time_added=current_time)
                for tag in tags:
                    tag = slugify(tag)
                    new_tag = Tag.objects.create(tag=tag, associated_post=new_post)
            return render(request, 'question.html', {'question':new_post, 'poster':poster, 'tags': tags, 'comments':None, 'logged_in':True})

        else: 
            return render(request, 'home.html', {'logged_in': False})
    else:
        if request.user.is_authenticated: 
            form = QuestionForm() 
            form2 = TagsForm() 
            return render(request, 'ask.html', {'logged_in': True, 'form':form, 'form2':form2}) 
        else:
            return render(request, 'home.html', {'logged_in':False}) 

@csrf_exempt
def get_question(request, title):
    logged_in = False
    if request.method == 'GET':
        try:
            # Check whether the user is currently logged in or not. If not, they will be treated as a guest and identified by IP
            if request.user.is_authenticated:
                logged_in = True
                tags = []
                media = []
                question = Post.objects.select_related('poster').get(slug = title)   
                #poster = Account.objects.get(account=question.poster) #get the Account as well as the associated foreign key info
                username = request.user.username
                # Retrieve account associated with logged in user from the database
                account = User.objects.get(username=username)
                # If the account has not viewed the current question, then increment the question's view count and add the account to the table of Viewer Accounts
                if not ViewerAccounts.objects.filter(viewer=account, post=question):
                    question.views += 1
                    question.save()
                    new_viewer = ViewerAccounts.objects.create(viewer = account, post = question)
                # retrieve set of tags and media from mysql
                tag_set = Tag.objects.filter(associated_post = question)
                for tag in tag_set:
                    added_tag = tag.tag
                    tags.append(added_tag) 
                comments = Comment.objects.select_related('poster').filter(post = question)
            else:
                tags = [] 
                # Get the current user's IP address
                ip_address = request.META['REMOTE_ADDR']
                question = Post.objects.select_related('poster').get(slug=title)   
                #poster =  question.poster
                # Check if the IP address is associated with this question in the database
                if not ViewerIP.objects.filter(ip_address = ip_address, post = question):
                    question.views += 1
                    question.save()
                    new_viewer = ViewerIP.objects.create(ip_address = ip_address, post = question)
                tag_set = Tag.objects.filter(associated_post = question) 
                for tag in tag_set:
                    tags.append(tag.tag) 
                comments = Comment.objects.select_related('poster').filter(post = question)
            return render(request, 'question.html', {'question':question, 'comments':comments, 'tags':tags, 'logged_in':logged_in})
        except Exception as e:
            print(e)
            data = {'status':'error', 'error':'Unable to retrive specified question'}
            return JsonResponse(data, status=401)
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
        if request.user.is_authenticated:
            #user = Account.objects.select_related('account').get(account = request.user)
            question = Post.objects.select_related('poster').get(slug = title)
            poster = Account.objects.get(account = question.poster) 
            json_data = json.loads(request.body.decode('utf-8'))  
            upvote = json_data['upvote'] 
            found_upvote = QuestionUpvotes.objects.filter(upvoter = request.user, question = question) 
            found_downvote = QuestionDownvotes.objects.filter(downvoter = request.user, question = question) 
            if found_upvote:
                # if upvote already exists in database, then undo the upvote
                question.score -= 1
                # decrement the poster's reputation if it is greater than 1 
                if question.poster.reputation > 1:
                    poster.reputation -= 1
                    poster.save() 
                found_upvote.delete()
                # if upvote parameter is false, then subtract 1 from upvote count and add a new downvote to database
                if not upvote: 
                    question.score -= 1 
                    QuestionDownvotes.objects.create(downvoter = request.user, question = question) # Create a new downvote in the system
                question.save() 
            elif found_downvote:
                # if a downvote from this user already exists, then undo the downvote
                question.score += 1
                # increment the reputation of the poster
                poster.reputation += 1
                poster.save() 
                found_downvote.delete() 
                # if the upvote parameter is true, then add 1 to upvote count and add a new upvote to the database 
                if upvote:
                    question.score += 1
                    QuestionUpvotes.objects.create(upvoter = request.user, question = question) 
                question.save() 
            else: 
                 # if no instances of an upvote/downvote for this question by this user was found, add upvote/downvote to table and make adjustments to question's score based on value of upvote
                if upvote: 
                    question.score += 1
                    poster.reputation += 1
                    poster.save()
                    question.save() 
                    QuestionUpvotes.objects.create(upvoter=request.user, question=question) 
                else:
                    question.score -= 1
                    if question.poster.reputation > 1:
                        poster.reputation -= 1
                        poster.save() 
                    question.save() 
                    QuestionDownvotes.objects.create(downvoter=request.user, question=question) 
            data = {'status' : 'OK'} 
            return JsonResponse(data) 
        else:
            data = {'status' : 'error'} 
            return JsonResponse(data, status=401) 

@csrf_exempt
def add_comment(request, title):
    # Check whether user is currently logged in 
    if request.user.is_authenticated:
        try:
            json_data = json.loads(request.body) 
            body = json_data['body']
            media = None
            if 'media' in json_data:
                media = json_data['media'] 
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
            media_objects = []
            if media != None:
                try:
                    for ids in media:
                        media_file = Media.objects.get(file_id=ids, uploader=account) 
                        media_objects.append(CommentMedia.objects.create(comment=new_comment, media=media_file))
                except Exception as e:
                    data = {'status':'error', 'error':'One of these media files does not belong to you or does not exist', 'id':''} 
                    new_comment.delete()
                    for objects in media_objects:
                        objects.delete() 
                    return JsonResponse(data, status=401) 
            data = {'status':'OK', 'id':comment_url, 'error':''} 
            return JsonResponse(data) 
        except Exception as e:
            print(e) 
            data = {'status':'error', 'id':'', 'error':'Error retrieving question'}
            return JsonResponse(data, status=401) 
    else:
        data = {'status' :'error', 'error':'You are not logged in'}
        return JsonResponse(data, status=401)

@csrf_exempt
def up_or_downvote_answer(request, url):
    data = {} 
    if request.method == 'POST':
        if request.user.is_authenticated:
            try:
                json_data = json.loads(request.body)
                comment = Comment.objects.get(comment_url=url) 
                user = Account.objects.get(username=request.session['username']) 
                upvote = json_data['upvote']
                found_upvote = CommentUpvotes.objects.filter(answer=comment, upvoter=user) 
                found_downvote = CommentDownvotes.objects.filter(answer=comment, downvoter=user) 
                if found_upvote:
                    comment.score -= 1
                    if comment.poster.reputation > 1:
                        comment.poster.reputation -= 1
                        comment.poster.save()
                    found_upvote.delete() 
                    if not upvote:
                        comment.score -= 1
                        CommentDownvotes.objects.create(answer=comment, downvoter=user) 
                    comment.save() 
                elif found_downvote:
                    comment.score += 1
                    comment.poster.reputation += 1
                    comment.poster.save() 
                    found_downvote.delete() 
                    if upvote:
                        comment.score += 1
                        CommentUpvotes.objects.create(answer=comment, upvoter=user) 
                    comment.save() 
                else: 
                    if upvote:
                        CommentUpvotes.objects.create(answer=comment, upvoter=user) 
                        comment.score += 1
                        comment.poster.reputation += 1
                        comment.poster.save() 
                        comment.save() 
                    else:
                        CommentDownvotes.objects.create(answer=comment, downvoter=user) 
                        comment.score -= 1
                        if comment.poster.reputation > 1:
                            comment.poster.reputation -= 1
                            comment.poster.save() 
                        comment.save()
                data['status'] = 'OK'
                return JsonResponse(data) 
            except Exception as e:
                print(e) 
                data['status'] = 'error'
                return JsonResponse(data, status=401) 
        else:
            data['status'] = 'error'
            data['error'] = 'You must be logged in to vote'
            return JsonResponse(data,status=401) 

@csrf_exempt
def accept_comment(request, url):
    if request.method == 'POST':
        if request.user.is_authenticated:
            try:
                answer = Comment.objects.get(comment_url=url) 
                question = answer.post
                if answer.post.poster.username != request.session['username'] or question.solved:
                    data = {'status': 'error'}
                    return JsonResponse(data, status=401)
                question.solved = True
                question.save()
                answer.accepted = True
                answer.save() 
                data = {'status':'OK'}
                return JsonResponse(data) 
            except Exception as e:
                print(e) 
                data = {'status':'error'}
                return JsonResponse(data, status_code=403) 
        else:
            return HttpResponse(status_code=403) 

@csrf_exempt
def get_comments(request, title):
    try:
        # Get the question corresponding to the title in URL
        question = Post.objects.get(slug=title)
        data = {}
        data['answers'] = []

        # Get all comments associated with the question
        all_comments = Comment.objects.filter(post=question).prefetch_related('poster') 
        for comment in all_comments:
            media = []
            all_media = CommentMedia.objects.filter(comment=comment).prefetch_related('media') 
            for medias in all_media:
                media.append(medias.media.file_id) 
            data['answers'].append({'id': comment.comment_url, 'user':comment.poster.username, 'body':comment.comment, 'score':comment.score, 'is_accepted':comment.accepted, 'timestamp':comment.time_posted, 'media':media})
        data['status'] = 'OK'
        data['error'] = ''
        return JsonResponse(data)
    except Exception as e:
        print(e)
        data = {'answers': [], 'status':'error', 'error':'error getting comments for question'}
        return JsonResponse(data, status=401)



@csrf_exempt
def search(request):
    try:
        logged_in = False 
        if request.user.is_authenticated:
            logged_in = True
        timestamp = datetime.datetime.now()
        # Default limit for number of returned questions
        limit = 25
        # Default search query
        search_query = ''
        # Default ordering
        order_by = "score"
        # tags to search for
        tags = []
        # has media
        has_media = False
        # question has only accepted answers
        accepted = False
        # If timestamp is in json request, then set timestamp to that
        if 'search_query' in request.POST:
            search_query = request.POST['search_query'] 
        if 'timestamp' in request.POST:
            timestamp = math.floor(request.POST['timestamp'])
        if 'limit' in request.POST:
            # If limit is in json data and is less than 100, then set limit to that
            if request.POST['limit'] > 100:
                limit = 100
            else:
                limit = request.POST['limit']
        if 'q' in request.POST:
            search_query = request.POST['q']
        if 'order_by' in request.POST:
            order_by = request.POST['order_by']
        if 'tags' in request.POST:
            tags = request.POST['tags']
        if 'has_media' in request.POST:
            has_media = request.POST['has_media']
        if 'accepted' in request.POST:
            accepted = request.POST['accepted']
        # Retrieve all questions which were added at or before the timestamp, depending on search query
        questions = None
        # using create_sql_statement create the search query based on the parameters specified
        sql_statement = create_search_query(tags, has_media, accepted, search_query, order_by, timestamp)
        print(sql_statement) 
        questions = Post.objects.raw(sql_statement)
        print(len(questions))
        return render(request, "results.html", {"logged_in": logged_in, "questions":questions}) 
    except Exception as e:
        print(e)
        data = {'status':'error', 'questions':[], 'error':'Trouble with your query'}
        return JsonResponse(data, status=401)
