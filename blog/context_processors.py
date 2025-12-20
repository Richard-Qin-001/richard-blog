from .models import Comment

def unread_notifications(request):
    if request.user.is_authenticated:
        count = Comment.objects.filter(
            parent__author=request.user, 
            is_read=False
        ).exclude(author=request.user).count()
        return {'unread_count': count}
    return {'unread_count': 0}