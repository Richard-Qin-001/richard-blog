from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import Post, Tag, Profile, Attachment, Message
from .forms import CommentForm, SignupForm, PostForm, Comment, ProfileForm
from django.shortcuts import redirect
from django.urls import reverse
from django.core.paginator import Paginator
from django.contrib.auth import login
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.auth.models import Group, User
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from django.db.models.functions import TruncDay
from django.views.decorators.csrf import csrf_exempt
from datetime import timedelta

def post_list(request, tag_name = None):
    query = request.GET.get('q')
    tag = None
    posts = Post.objects.filter(published_date__lte=timezone.now())

    if tag_name:
        tag = get_object_or_404(Tag, name = tag_name)
        posts = posts.filter(tags=tag)
    if query:
        posts = posts.filter(Q(title__icontains=query) | Q(text__icontains=query), published_date__isnull=False).distinct()
    posts = posts.order_by('-published_date')
    paginator = Paginator(posts, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'blog/post_list.html', {
        'page_obj': page_obj,
        'query':query,
        'tag': tag,
        })

@staff_member_required
def tag_delete(request, pk):
    tag = get_object_or_404(Tag, pk=pk)
    tag.delete()
    return redirect('post_list')

def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        if not request.user.has_perm('blog.add_comment'):
            from django.contrib import messages
            messages.error(request, "Your group does not have permission to post comments.")
            return redirect('post_detail', pk=post.pk)
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            parent_id = request.POST.get('parent_id')
            if parent_id:
                from .models import Comment
                comment.parent = Comment.objects.get(id=parent_id)
            comment.save()

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'comment_id': comment.id,
                    'author_nickname': comment.author.profile.nickname or comment.author.username,
                    'author_username': comment.author.username,
                    'text': comment.text,
                    'created_date': comment.created_date.strftime('%Y-%m-%d %H:%M'),
                    'avatar_url': comment.author.profile.avatar.url if comment.author.profile.avatar else '/static/images/default.png',
                    'parent_id': parent_id
                })
            return redirect(f"{reverse('post_detail', kwargs={'pk': post.pk})}#comments")
    else:
        form = CommentForm()
    return render(request, 'blog/post_detail.html', {'post': post, 'form': form})


@permission_required('blog.add_post', raise_exception=True)
def post_new(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.published_date = timezone.now()
            post.save()
            form.save()
            files = request.FILES.getlist('attachments')
            for f in files:
                Attachment.objects.create(post=post, file=f)
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm()
    return render(request, 'blog/post_edit.html', {'form': form})

@permission_required('blog.add_post', raise_exception=True)
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    can_change = request.user.has_perm('blog.change_post')
    
    if (can_change and request.user == post.author) or request.user.is_superuser:
        if request.method == "POST":
            form = PostForm(request.POST, request.FILES, instance=post)
            if form.is_valid():
                post = form.save()
                files = request.FILES.getlist('attachments')
                for f in files:
                    Attachment.objects.create(post=post, file=f)
                messages.success(request, "文章更新成功！")
                return redirect('post_detail', pk=post.pk)
        else:
            form = PostForm(instance=post)
        return render(request, 'blog/post_edit.html', {'form': form})
    else:
        messages.error(request, "你没有权限编辑这篇文章。")
        return redirect('post_detail', pk=post.pk)

@login_required
def post_remove(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.user == post.author or request.user.is_superuser:
        post.delete()
        return redirect('post_list')
    else:
        return redirect('post_detail', pk=post.pk)
    
@login_required
def post_like(request, pk):
    post = get_object_or_404(Post, id=pk)
    if post.likes.filter(id=request.user.id).exists():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True
    return JsonResponse({'liked': liked, 'count': post.total_likes()})

@login_required
def attachment_delete(request, pk):
    attachment = get_object_or_404(Attachment, pk = pk)
    if request.user == attachment.post.author or request.user.is_superuser:
        attachment.delete()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error', 'message': '没有权限'}, status=403)

@csrf_exempt
@login_required
def api_image_upload(request):
    if request.method == "POST" and request.FILES.get('image'):
        img = request.FILES['image']
        instance = Attachment.objects.create(file=img)
        return JsonResponse({
            'success': True,
            'url': instance.file.url
        })
    return JsonResponse({'success': False}, status=400)



    
@login_required
def comment_remove(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    post_pk = comment.post.pk
    can_delete = (
        comment.author == request.user or 
        request.user.is_superuser or 
        request.user.has_perm('blog.delete_comment')
    )
    if can_delete:
        comment.delete()
        messages.success(request, "评论已成功删除。")
    else:
        messages.error(request, "您没有权限删除此评论。")
    return redirect('post_detail', pk=post_pk)


@login_required
def comment_edit(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if request.user.username != comment.author and not request.user.is_superuser:
        return redirect('post_detail', pk=comment.post.pk)
    
    if request.method == "POST":
        new_text = request.POST.get('text')
        if new_text:
            comment.text = new_text
            comment.save()
            return redirect(f"{reverse('post_detail', kwargs={'pk': comment.post.pk})}#comment-{comment.id}")
    
    return redirect('post_detail', pk=comment.post.pk)

@login_required
def comment_like(request, pk):
    comment = get_object_or_404(Comment, id=pk)
    if comment.likes.filter(id=request.user.id).exists():
        comment.likes.remove(request.user)
        liked = False
    else:
        comment.likes.add(request.user)
        liked = True
    return JsonResponse({'liked': liked, 'count': comment.total_likes()})





def signup(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            try:
                default_group = Group.objects.get(name='Guests')
                user.groups.add(default_group)
            except Group.DoesNotExist:
                pass
                
            login(request, user, backend='blog.backends.EmailOrUsernameBackend')
            return redirect('post_list')
    else:
        form = SignupForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def profile_edit(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, f"太棒了，{profile.nickname}！您的个人资料已更新。")
            return redirect('post_list')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'user/profile_edit.html', {'form': form})

def password_recovery(request):
    if request.method == "POST":
        username = request.POST.get('username')
        key = request.POST.get('recovery_key').strip().upper()
        new_password = request.POST.get('new_password')
        
        try:
            user = User.objects.get(username=username)
            if user.profile.recovery_key == key:
                user.set_password(new_password)
                user.save()
                messages.success(request, "密码已通过密钥重置成功，请重新登录！")
                return redirect('login')
            else:
                messages.error(request, "恢复密钥不正确。")
        except User.DoesNotExist:
            messages.error(request, "该用户名不存在。")
            
    return render(request, 'registration/password_recovery.html')

def user_list(request):
    users = User.objects.annotate(post_count=Count('post')).select_related('profile').order_by('-date_joined')
    return render(request, 'user/user_list.html', {'users': users})

def profile_public(request, username):
    profile_user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=profile_user).order_by('-published_date')
    comment_count = Comment.objects.filter(author=profile_user).count()
    recent_comments = Comment.objects.filter(author=profile_user).select_related('post').order_by('-created_date')[:10]

    unread_replies = []
    if request.user == profile_user:
        unread_replies = list(Comment.objects.filter(
            parent__author=request.user, 
            is_read=False
        ).exclude(author=request.user).select_related('post', 'author'))
        Comment.objects.filter(parent__author=request.user, is_read=False).update(is_read=True)

    one_year_ago = timezone.now() - timedelta(days=365)
    post_activity = Post.objects.filter(author=profile_user, created_date__gte=one_year_ago) \
        .annotate(day=TruncDay('created_date')) \
        .values('day') \
        .annotate(count=Count('id'))
    
    comment_activity = Comment.objects.filter(author=profile_user, created_date__gte=one_year_ago) \
        .annotate(day=TruncDay('created_date')) \
        .values('day') \
        .annotate(count=Count('id'))
    activity_data = {}
    for entry in post_activity:
        day_str = entry['day'].strftime('%Y-%m-%d')
        activity_data[day_str] = activity_data.get(day_str, 0) + entry['count']
    for entry in comment_activity:
        day_str = entry['day'].strftime('%Y-%m-%d')
        activity_data[day_str] = activity_data.get(day_str, 0) + entry['count']
    
    return render(request, 'user/profile.html', {
        'profile_user': profile_user,
        'posts': posts,
        'recent_comments': recent_comments,
        'unread_replies': unread_replies,
        'comment_count': comment_count,
        'activity_data': activity_data,
    })

@login_required
def inbox(request):
    received_messages = Message.objects.filter(recipient=request.user, deleted_by_recipient=False)
    sent_messages = Message.objects.filter(sender=request.user, deleted_by_sender=False)
    all_replies_qs = Comment.objects.filter(
        Q(post__author=request.user) | Q(parent__author=request.user)
    ).exclude(author=request.user).distinct().order_by('-created_date')
    replies_list = list(all_replies_qs)
    all_replies_qs.filter(is_read=False).update(is_read=True)
    return render(request, 'user/inbox.html', {
        'received_messages' : received_messages,
        'sent_messages' : sent_messages,
        'unread_replies': replies_list,
    })

@login_required
def message_detail(request, pk):
    msg_obj = get_object_or_404(Message, pk = pk)
    if msg_obj.sender != request.user and msg_obj.recipient != request.user:
        return redirect('inbox')
    
    if request.method == "POST":
        if msg_obj.sender == request.user:
            msg_obj.deleted_by_sender = True
        if msg_obj.recipient == request.user:
            msg_obj.deleted_by_recipient = True
        
        msg_obj.save()
        if msg_obj.deleted_by_sender and msg_obj.deleted_by_recipient:
            msg_obj.delete()
            
        return redirect('inbox')

    if msg_obj.recipient == request.user and not msg_obj.is_read:
        msg_obj.is_read = True
        msg_obj.save()
    return render(request, "user/message_detail.html", {'message' : msg_obj})

@login_required
def send_message(request, recipient_id):
    recipient   = get_object_or_404(User, id=recipient_id)
    if request.method == "POST":
        subject = request.POST.get('subject')
        body = request.POST.get('body')
        Message.objects.create(
            sender=request.user, 
            recipient=recipient, 
            subject=subject, 
            body=body
        )
        return redirect('inbox')
    return render(request, 'user/send_message.html', {'recipient': recipient})