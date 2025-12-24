from django import forms
from .models import Comment, Tag, Post, Profile
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from captcha.fields import CaptchaField

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control', 
                'placeholder': '在此输入您的评论...',
                'rows': 3,
                'style': 'width: 100%; border-radius: 10px; padding: 10px;'
            }),
        }

class SignupForm(UserCreationForm):

    email = forms.EmailField(required=False, help_text="可选。若填写，之后可用邮箱登录")
    captcha = CaptchaField(label='验证码')

    class Meta:
        model = User
        fields = ('username', 'email', )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            if User.objects.filter(email=email).exists():
                raise ValidationError("该邮箱已被其他账号注册。")
        return email

class PostForm(forms.ModelForm):   
    tags = forms.CharField(
        required=False,
        label="文章标签",
        widget=forms.SelectMultiple(attrs={'class': 'select2-tags'})
    )
    class Meta:
        model = Post
        fields = ('title', 'text', 'tags',)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tags'].widget.choices = [(t.name, t.name) for t in Tag.objects.all()]
        if self.instance.pk:
            self.initial['tags'] = [t.name for t in self.instance.tags.all()]
        
    def save(self, commit = True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        
        if instance.pk:
            instance.tags.clear()
            tag_names = self.data.getlist('tags')
            for name in tag_names:
                if name.strip():
                    tag_obj, _ = Tag.objects.get_or_create(name=name.strip())
                    instance.tags.add(tag_obj)
        return instance

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('nickname', 'gender', 'birthday', 'bio', 'avatar')
        widgets = {
            'nickname': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'birthday': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }
    