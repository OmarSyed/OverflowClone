from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Post, Tag 
from django.utils.translation import gettext_lazy as _

class SignUpForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2',)

class VerificationForm(forms.Form):
    email = forms.EmailField() 
    key = forms.CharField(max_length=12) 

    def clean(self):
        cleaned_data = super(VerificationForm, self).clean() 
        email = cleaned_data.get('email') 
        key = cleaned_data.get('key') 
        if not email and not key:
            raise forms.ValidationError('Please enter a value in the fields') 

class LogInForm(forms.ModelForm):

    def clean(self):
        cleaned_data = super(LogInForm, self).clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password') 

    class Meta:
        model = User
        fields = ('username', 'password', )
        widgets = {'password':forms.PasswordInput(), }

class QuestionForm(forms.ModelForm):

    def clean(self):
        super().clean() 

    class Meta:
        model = Post
        fields = ('title', 'body') 
        widgets = {
                'body': forms.widgets.Textarea({'cols':'60', 'rows': '20'}),
        }
        error_messages = {
                'title': {
                    'max_length': _('Please shorten the title'),
                },
                'body': {
                    'max_length': _('You have exceeded the max number of characters in the body'),
                }
        }

class TagsForm(forms.ModelForm):

    def clean(self):
        super().clean() 

    class Meta: 
        model = Tag
        fields = ('tag', ) 
        widgets = {
                'tag':forms.widgets.TextInput(),
        }
        error_messages = {
                'tag': {
                    'max_length':_('Max length of tag name reached'), 
                }
        }

