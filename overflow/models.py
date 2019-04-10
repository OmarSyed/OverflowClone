from django.db import models
from django.urls import reverse
from django.template.defaultfilters import slugify
from django_unixdatetimefield import UnixDateTimeField
from django.utils.crypto import get_random_string

# Create your models here.
class Account(models.Model):
    account_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    email = models.EmailField()
    verification_key = models.CharField(max_length=12, default='abracadabraa') 
    verified = models.BooleanField(default=False)
    reputation = models.IntegerField(default=1) 

class Post(models.Model):
    post_id = models.AutoField(primary_key=True) 
    poster = models.ForeignKey(Account, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    body = models.TextField() 
    views = models.IntegerField(default=0)
    answer_count = models.IntegerField(default=0)
    score = models.IntegerField(default=0)
    slug = models.SlugField(max_length=255)
    time_added = models.IntegerField(default=0)  
    
    def get_absolute_url(self):
        return reverse('exact_post', kwargs={'slug' : self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super(Post, self).save(*args, **kwargs)

    class Meta:
        ordering = ['time_added']
        def __unicode__(self):
            return self.title


class Comment(models.Model):
    comment_id = models.AutoField(primary_key=True)
    comment_url = models.CharField(max_length=15, null=False, default=get_random_string(length=15))
    poster = models.ForeignKey(Account, on_delete=models.CASCADE) 
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    comment = models.TextField() 
    score = models.IntegerField(default=0) 
    time_posted = models.IntegerField(default=0) 
    accepted = models.BooleanField(default=False) 

# Maintain a table of tags associated with individual posts
class Tag(models.Model):
    associated_post = models.ForeignKey(Post, on_delete=models.CASCADE)
    tag = models.CharField(max_length=100)

# IP addresses that have viewed a question
class ViewerIP(models.Model):
    ip_address = models.CharField(max_length=32) 
    post = models.ForeignKey(Post, on_delete=models.CASCADE) 

# Accounts that have viewed a question
class ViewerAccounts(models.Model):
    viewer = models.ForeignKey(Account, on_delete=models.CASCADE) 
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

#Maps question upvotes to accounts
class QuestionUpvotes(models.Model):
    upvoter = models.ForeignKey(Account, on_delete = models.CASCADE) 
    question = models.ForeignKey(Post, on_delete = models.CASCADE) 

#Maps question downvotes to accounts
class QuestionDownvotes(models.Model):
    downvoter = models.ForeignKey(Account, on_delete = models.CASCADE)
    question = models.ForeignKey(Post, on_delete = models.CASCADE) 

#Maps comment upvotes to accounts
class CommentUpvotes(models.Model):
    upvoter = models.ForeignKey(Account, on_delete= models.CASCADE) 
    answer = models.ForeignKey(Comment, on_delete = models.CASCADE) 

#Maps comment downvotes to accounts
class CommentDownvotes(models.Model):
    downvoter = models.ForeignKey(Account, on_delete = models.CASCADE)
    answer = models.ForeignKey(Comment, on_delete = models.CASCADE) 
