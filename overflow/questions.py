from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from .models import Account, Post, Comment, Tag, ViewerAccounts, ViewerIP, QuestionUpvotes, QuestionDownvotes, CommentUpvotes, CommentDownvotes, Media, QuestionMedia, CommentMedia
import json
import operator
from functools import reduce
from random import choice
from string import ascii_uppercase
import math
import datetime

def create_search_query(tags, has_media, accepted, query, sort_by, timestamp):
    sql_statement = 'SELECT * FROM overflow_post WHERE time_added <= '+str(timestamp)
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


@csrf_exempt
def add_question(request):
    new_post = None
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
            media = None
            if 'media' in json_data:
                media = json_data['media'] 
            # Get the account associated with the current user's session
            account = Account.objects.get(username=request.session['username'])
            timeadded = math.floor(datetime.datetime.utcnow().timestamp() - 14400)
            if media != None:
                new_post = Post.objects.create(poster=account, title=title, body=body, time_added=timeadded, has_media=True)
                try:
                    for ids in media:
                        retrieved_media = Media.objects.get(file_id = ids, uploader=account)
                        QuestionMedia.objects.create(question=new_post, media=retrieved_media)
                except Exception as e:
                    print (e)
                    data = {'status':'error', 'error':'One of the media files either does not belong to you or does not exist'}
                    new_post.delete()
                    return JsonResponse(data, status=401)
            else:
                new_post = Post.objects.create(poster=account, title=title, body=body, time_added=timeadded) 
            # Add a new question to the database with user account associated with the question
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
            #print(data)
            return JsonResponse(data, status=401)
    else:
        data = {'status': 'error', 'error': 'You are not logged in'}
        #print(data) 
        return JsonResponse(data, status=401)

@csrf_exempt
def get_question(request, title):
    if request.method == 'GET':
        try:
            # Check whether the user is currently logged in or not. If not, they will be treated as a guest and identified by IP
            if 'username' in request.session:
                tags = []
                media = []
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
                # retrieve set of tags and media from mysql
                tag_set = Tag.objects.filter(associated_post = question)
                media_set = QuestionMedia.objects.filter(question=question).prefetch_related('media')
                for tag in tag_set:
                    added_tag = tag.tag
                    tags.append(added_tag)
                for medias in media_set:
                    media.append(medias.media.file_id) # append all related media ids 
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
                data['question'] = {'id': id_, 'user':{'username':question.poster.username, 'reputation':question.poster.reputation},'title':title, 'body': body, 'score':question.score, 'view_count':question.views, 'answer_count': question.answer_count, 'timestamp': question.time_added, 'media':media, 'tags':tags, 'accepted_answer_id':answer_id}
                data['error'] = ''
                return JsonResponse(data)
            else:
                tags = []
                media = [] 
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
                media_set = QuestionMedia.objects.filter(question = question).prefetch_related('media') 
                for tag in tag_set:
                    #print(tag.tag)
                    tags.append(tag.tag)
                for medias in media_set:
                    media.append(medias.media.file_id) 
                accepted_answer = Comment.objects.filter(post = question, accepted = True)
                answer_id = None
                if not accepted_answer:
                    answer_id = 'Null'
                else:
                    answer_id = accepted_answer.comment_id 
                data = {}
                data['status'] = 'OK'
                data['question'] = {'id': question.slug, 'user':{'username':question.poster.username, 'reputation':question.poster.reputation},'title': question.title, 'score':question.score, 'body': question.body, 'view_count':question.views, 'answer_count': question.answer_count, 'timestamp': question.time_added, 'media':media, 'tags':tags, 'accepted_answer_id':answer_id}
                data['error'] = ''
                return JsonResponse(data)
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
        if 'username' in request.session:
            user = Account.objects.get(username = request.session['username'])
            question = Post.objects.get(slug = title)  
            json_data = json.loads(request.body) 
            upvote = json_data['upvote'] 
            found_upvote = QuestionUpvotes.objects.filter(upvoter = user, question = question) 
            found_downvote = QuestionDownvotes.objects.filter(downvoter = user, question = question) 
            if found_upvote:
                # if upvote already exists in database, then undo the upvote
                question.score -= 1
                # decrement the poster's reputation if it is greater than 1 
                if question.poster.reputation > 1:
                    question.poster.reputation -= 1
                    question.poster.save() 
                found_upvote.delete()
                # if upvote parameter is false, then subtract 1 from upvote count and add a new downvote to database
                if not upvote: 
                    question.score -= 1 
                    QuestionDownvotes.objects.create(downvoter = user, question = question) # Create a new downvote in the system
                question.save() 
            elif found_downvote:
                # if a downvote from this user already exists, then undo the downvote
                question.score += 1
                # increment the reputation of the poster
                question.poster.reputation += 1
                question.poster.save() 
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
                    question.poster.reputation += 1
                    question.poster.save()
                    question.save() 
                    QuestionUpvotes.objects.create(upvoter=user, question=question) 
                else:
                    question.score -= 1
                    if question.poster.reputation > 1:
                        question.poster.reputation -= 1
                        question.poster.save() 
                    question.save() 
                    QuestionDownvotes.objects.create(downvoter=user, question=question) 
            data = {'status' : 'OK'} 
            return JsonResponse(data) 
        else:
            data = {'status' : 'error'} 
            return JsonResponse(data, status=401) 

@csrf_exempt
def add_comment(request, title):
    # Check whether user is currently logged in 
    if 'username' in request.session:
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
        if 'username' in request.session:
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
        timestamp = math.floor(datetime.datetime.utcnow().timestamp() - 14400)
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
        json_data = json.loads(request.body)
        print(json_data)
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
        if 'order_by' in json_data:
            order_by = json_data['order_by']
        if 'tags' in json_data:
            tags = json_data['tags']
        if 'has_media' in json_data:
            has_media = json_data['has_media']
        if 'accepted' in json_data:
            accepted = json_data['accepted']
        data = {}
        data['status'] = 'OK'
        data['questions'] = []
        # Keep track of how many question you return
        i = 0
        # Retrieve all questions which were added at or before the timestamp, depending on search query
        questions = None
        # using create_sql_statement
        sql_statement = create_search_query(tags, has_media, accepted, search_query, order_by, timestamp)
        print(sql_statement)
        questions = Post.objects.raw(sql_statement)
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
                accepted_answer_id = associated_comments[0].comment_url
            else:
                accepted_answer_id = 'Null'
            media = []
            all_media = QuestionMedia.objects.filter(question=question).prefetch_related('media')
            for medias in all_media:
                media.append(medias.media.file_id)
            data['questions'].append({'id':question.slug, 'user': {'username':question.poster.username, 'reputation':question.poster.reputation}, 'title':question.title, 'body':question.body, 'score':question.score, 'view_count':question.views, 'answer_count':question.answer_count, 'timestamp':question.time_added, 'media': media, 'tags': tags, 'accepted_answer_id':accepted_answer_id})
            i += 1
        data['error'] = ''
       #for a in data['questions']:
        print(len(data['questions']))
        return JsonResponse(data)
    except Exception as e:
        print(e)
        data = {'status':'error', 'questions':[], 'error':'Trouble with your query'}
        return JsonResponse(data, status=401)
