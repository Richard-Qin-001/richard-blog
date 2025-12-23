from .models import Comment, Message
from django.db.models import Q

def unread_notifications(request):
    if request.user.is_authenticated:
        unread_comment_count = Comment.objects.filter(Q(post__author=request.user) | Q(parent__author=request.user),is_read=False
        ).exclude(author=request.user).distinct().count()

        unread_msg_count = Message.objects.filter(
            recipient=request.user, 
            is_read=False,
            deleted_by_recipient=False
        ).count()

        return {
            'unread_comment_count': unread_comment_count,
            'unread_msg_count': unread_msg_count,
            'total_unread_count': unread_comment_count + unread_msg_count
        }
    return {'unread_comment_count': 0, 'unread_msg_count': 0, 'total_unread_count': 0}