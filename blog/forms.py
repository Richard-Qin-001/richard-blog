from django import forms
from .models import Comment, Tag, Post, Profile
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('author', 'text',)

class SignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email')

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
    