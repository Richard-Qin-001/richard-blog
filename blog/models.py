from django.db import models
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image
import uuid

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Post(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="作者")
    title = models.CharField(max_length=200)
    text = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)
    published_date = models.DateTimeField(blank=True, null=True)
    likes = models.ManyToManyField(User, related_name='blog_posts', blank=True)
    tags = models.ManyToManyField(Tag, related_name='posts', blank=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def publish(self):
        self.published_date = timezone.now()
        self.save()
    
    def total_likes(self):
        return self.likes.count()
    
    def __str__(self):
        return self.title
    
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    likes = models.ManyToManyField(User, related_name='comment_likes', blank=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return self.text
    
    def total_likes(self):
        return self.likes.count()
    
class Profile(models.Model):
    GENDER_CHOICES = (
        ('M', '男'),
        ('F', '女'),
        ('O', '其他'),
        ('U', '保密'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    nickname = models.CharField(max_length=50, blank=True, verbose_name="昵称")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='U', verbose_name="性别")
    birthday = models.DateField(null=True, blank=True, verbose_name="生日")
    bio = models.TextField(max_length=500, blank=True, verbose_name="个人简介")
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.png', blank=True, verbose_name="头像")
    recovery_key = models.CharField(max_length=50, blank=True, unique=True, null=True, verbose_name="恢复密钥")

    def __str__(self):
        return self.nickname or self.user.username
    
    def save(self, *args, **kwargs):
        if not self.recovery_key:
            self.recovery_key = str(uuid.uuid4()).replace('-', '').upper()[:16]
        super().save(*args, **kwargs)

        if self.avatar:
            img_path = self.avatar.path
            img = Image.open(img_path)
            if img.height > 200 or img.width > 200:
                width, height = img.size
                min_side = min(width, height)
                left = (width - min_side) / 2
                top = (height - min_side) / 2
                right = (width + min_side) / 2
                bottom = (height + min_side) / 2

                img = img.crop((left, top, right, bottom))
                img.thumbnail((200, 200), Image.LANCZOS)
                img.save(img_path, quality=85)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance, nickname=instance.username)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Attachment(models.Model):
    post = models.ForeignKey(Post, related_name='attachments', on_delete=models.CASCADE, null=True, blank=True)
    file = models.FileField(upload_to='attachments/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name