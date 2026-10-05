from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from decimal import Decimal

from notifications.models import Notification
from resources.models import ResourceConflict
from expenses.models import Expense

@login_required
def list_notifications(request):
    filter_type = request.GET.get('type', '').strip()
    filter_severity = request.GET.get('severity', '').strip()
    unread_only = request.GET.get('unread', '') == '1'
    q = request.GET.get('q', '').strip()

    notifications_qs = Notification.objects.all().order_by('-created_at')

    if filter_type:
        notifications_qs = notifications_qs.filter(notification_type=filter_type)
    if filter_severity:
        notifications_qs = notifications_qs.filter(severity=filter_severity)
    if unread_only:
        notifications_qs = notifications_qs.filter(is_read=False)
    if q:
        notifications_qs = notifications_qs.filter(
            Q(title__icontains=q) |
            Q(message__icontains=q) |
            Q(source_code__icontains=q)
        )

    # 4 Metric Overview Bar Counts
    critical_collisions_count = ResourceConflict.objects.filter(is_resolved=False).count()
    awaiting_approval_qs = Expense.objects.filter(amount__gte=Decimal('5000.00'), is_authorized=False).exclude(payment_status='Cancelled')
    awaiting_approval_count = awaiting_approval_qs.count()
    pending_approval_amount = sum((exp.amount for exp in awaiting_approval_qs), Decimal('0.00'))

    today_logs_count = Notification.objects.filter(created_at__date=timezone.now().date()).count()

    context = {
        'page_title': 'Notifications & Alert Dispatch Center',
        'notifications': notifications_qs,
        'filter_type': filter_type,
        'filter_severity': filter_severity,
        'unread_only': unread_only,
        'q': q,
        # 4 Metric Cards
        'critical_collisions_count': critical_collisions_count,
        'awaiting_approval_count': awaiting_approval_count,
        'pending_approval_amount': pending_approval_amount,
        'today_logs_count': today_logs_count,
    }
    return render(request, 'notifications/list.html', context)

@login_required
def mark_notification_read(request, notification_id):
    if request.method == 'POST':
        notification = get_object_or_404(Notification, id=notification_id)
        notification.is_read = True
        notification.save()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'notification_id': notification_id})
        messages.success(request, f"Notification marked as read.")
    return redirect('notifications:list')

@login_required
def mark_all_read(request):
    if request.method == 'POST':
        Notification.objects.filter(is_read=False).update(is_read=True)
        messages.success(request, "All notifications marked as read.")
    return redirect('notifications:list')

@login_required
def broadcast_urgent(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        message = request.POST.get('message', '').strip()
        notification_type = request.POST.get('notification_type', 'general')
        severity = request.POST.get('severity', 'critical')
        link_url = request.POST.get('link_url', '').strip()

        if title and message:
            Notification.objects.create(
                title=title,
                message=message,
                notification_type=notification_type,
                severity=severity,
                source_code='URGENT_BROADCAST',
                link_url=link_url,
                is_read=False
            )
            messages.success(request, f"Urgent broadcast '{title}' dispatched across campus dispatch channels.")
        else:
            messages.error(request, "Title and message are required for broadcasts.")
    return redirect('notifications:list')
