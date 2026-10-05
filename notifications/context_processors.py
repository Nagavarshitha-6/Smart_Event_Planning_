def notification_badge_processor(request):
    """
    Context processor to provide unread notification count and conflict alert counts across all views.
    """
    if request.user.is_authenticated:
        try:
            from notifications.models import Notification
            unread_count = Notification.objects.filter(is_read=False).count()
        except Exception:
            unread_count = 0
            
        try:
            from resources.models import ResourceConflict
            conflict_count = ResourceConflict.objects.filter(is_resolved=False).count()
        except Exception:
            conflict_count = 0
            
        return {
            'unread_notifications_count': unread_count,
            'active_conflicts_count': conflict_count,
        }
    return {
        'unread_notifications_count': 0,
        'active_conflicts_count': 0,
    }
