from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import Post, Tag, Profile
from .forms import CommentForm, SignupForm, PostForm, Comment, ProfileForm
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import login
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.auth.models import Group, User
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q

def post_list(request, tag_name = None):
    query = request.GET.get('q')
    posts = Post.objects.filter(published_date__lte=timezone.now())

    if tag_name:
        tag = get_object_or_404(Tag, name = tag_name)
        posts = posts.filter(tags=tag)
    if query:
        posts = posts.filter(Q(title__icontains=query) | Q(text__icontains=query), published_date__isnull=False).distinct()
    posts = posts.order_by('published_date')
    return render(request, 'blog/post_list.html', {'posts' : posts})

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
            comment.author = request.user.username
            parent_id = request.POST.get('parent_id')
            if parent_id:
                from .models import Comment
                comment.parent = Comment.objects.get(id=parent_id)
            comment.save()
            return redirect(f"{reverse('post_detail', kwargs={'pk': post.pk})}#comments")
    else:
        form = CommentForm()
    return render(request, 'blog/post_detail.html', {'post': post, 'form': form})


@permission_required('blog.add_post', raise_exception=True)
def post_new(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.published_date = timezone.now()
            post.save()
            form.save()
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
            form = PostForm(request.POST, instance=post)
            if form.is_valid():
                post = form.save()
                return redirect('post_detail', pk=post.pk)
        else:
            form = PostForm(instance=post)
        return render(request, 'blog/post_edit.html', {'form': form})
    else:
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
def comment_remove(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    post_pk = comment.post.pk
    if request.user.username == comment.author or request.user.is_superuser:
        comment.delete()
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
    return render(request, 'blog/profile_edit.html', {'form': form})

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