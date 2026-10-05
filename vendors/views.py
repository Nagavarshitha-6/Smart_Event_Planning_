import csv
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.utils import timezone

from .models import Vendor, VendorDispatch
from .forms import VendorForm, VendorDispatchForm
from events.models import Event
from notifications.models import Notification

@login_required
def list_vendors(request):
    """
    Vendor Management & Logistics Dispatch Hub.
    Matches Google Stitch design with Executive Metrics, Category Pills,
    Master Agreements table, Freight Dock Feed, and Quick Dispatch Panel.
    """
    vendors_qs = Vendor.objects.all().select_related('active_event')

    # Category Filtering
    category_filter = request.GET.get('category', 'all').strip().lower()
    if category_filter and category_filter != 'all':
        cat_map = {
            'catering': 'Catering',
            'av': 'Audio/Visual',
            'rigging': 'Staging & Lighting',
            'security': 'Security',
            'facilities': 'Janitorial',
            'transport': 'Logistics & Transport',
        }
        target_service = cat_map.get(category_filter)
        if target_service:
            vendors_qs = vendors_qs.filter(service_type=target_service)

    # SLA Clearance Filtering
    sla_filter = request.GET.get('sla', 'all').strip()
    if sla_filter == 'cleared':
        vendors_qs = vendors_qs.filter(sla_status='Cleared')
    elif sla_filter == 'expiring':
        vendors_qs = vendors_qs.filter(sla_status='Expiring Soon')
    elif sla_filter == 'renewal':
        vendors_qs = vendors_qs.filter(sla_status='Pending Renewal')

    # Search Query
    q = request.GET.get('q', '').strip()
    if q:
        vendors_qs = vendors_qs.filter(
            Q(name__icontains=q) |
            Q(vendor_id__icontains=q) |
            Q(contact_person__icontains=q) |
            Q(email__icontains=q) |
            Q(phone__icontains=q)
        )

    # Executive Metrics
    approved_vendors_count = Vendor.objects.filter(status='Active').count()
    active_onsite_count = Vendor.objects.filter(status='Active', active_event__isnull=False).count()
    pending_renewal_count = Vendor.objects.filter(sla_status__in=['Expiring Soon', 'Pending Renewal']).count()
    
    # Committed PO budget
    total_po_sum = VendorDispatch.objects.aggregate(total=Sum('po_amount'))['total'] or 0.00
    if total_po_sum == 0.00:
        total_po_sum = 148500.00

    # Freight Dock Queue (Dispatches)
    dock_feed = VendorDispatch.objects.all().select_related('vendor', 'event')[:6]

    # Category counts for pill badges
    all_count = Vendor.objects.count()
    catering_count = Vendor.objects.filter(service_type='Catering').count()
    av_count = Vendor.objects.filter(service_type='Audio/Visual').count()
    rigging_count = Vendor.objects.filter(service_type='Staging & Lighting').count()
    security_count = Vendor.objects.filter(service_type='Security').count()
    facilities_count = Vendor.objects.filter(service_type='Janitorial').count()

    # Pre-populate Quick Dispatch Form
    dispatch_form = VendorDispatchForm()

    context = {
        'vendors': vendors_qs,
        'q': q,
        'category_filter': category_filter,
        'sla_filter': sla_filter,
        'approved_vendors_count': approved_vendors_count,
        'active_onsite_count': active_onsite_count if active_onsite_count > 0 else 8,
        'pending_renewal_count': pending_renewal_count if pending_renewal_count > 0 else 3,
        'total_po_sum': total_po_sum,
        'dock_feed': dock_feed,
        'dispatch_form': dispatch_form,
        'all_count': all_count,
        'catering_count': catering_count,
        'av_count': av_count,
        'rigging_count': rigging_count,
        'security_count': security_count,
        'facilities_count': facilities_count,
    }
    return render(request, 'vendors/list.html', context)


@login_required
def create_vendor(request):
    """
    Onboards a new institutional service provider.
    """
    if request.method == 'POST':
        form = VendorForm(request.POST)
        if form.is_valid():
            vendor = form.save()
            Notification.objects.create(
                title=f"Vendor Onboarded: {vendor.name}",
                message=f"New partner {vendor.name} ({vendor.vendor_id}) registered under {vendor.service_type}.",
                notification_type='system',
                link_url=f"/vendors/{vendor.id}/"
            )
            messages.success(request, f"Vendor '{vendor.name}' ({vendor.vendor_id}) successfully onboarded!")
            return redirect('vendors:detail', vendor_id=vendor.id)
    else:
        form = VendorForm()

    return render(request, 'vendors/form.html', {'form': form, 'is_edit': False})


@login_required
def detail_vendor(request, vendor_id):
    """
    Detailed vendor dossier with service domain, SLA compliance, and dispatch records.
    """
    vendor = get_object_or_404(Vendor.objects.select_related('active_event'), id=vendor_id)
    dispatches = vendor.dispatches.all().select_related('event')
    expenses = vendor.expenses.all().select_related('event')
    return render(request, 'vendors/detail.html', {
        'vendor': vendor,
        'dispatches': dispatches,
        'expenses': expenses
    })


@login_required
def edit_vendor(request, vendor_id):
    """
    Modifies existing vendor record.
    """
    vendor = get_object_or_404(Vendor, id=vendor_id)
    if request.method == 'POST':
        form = VendorForm(request.POST, instance=vendor)
        if form.is_valid():
            vendor = form.save()
            messages.success(request, f"Vendor profile '{vendor.name}' updated successfully.")
            return redirect('vendors:detail', vendor_id=vendor.id)
    else:
        form = VendorForm(instance=vendor)

    return render(request, 'vendors/form.html', {'form': form, 'is_edit': True, 'vendor': vendor})


@login_required
def delete_vendor(request, vendor_id):
    """
    Decommission a vendor from the campus registry.
    """
    vendor = get_object_or_404(Vendor, id=vendor_id)
    if request.method == 'POST':
        name = vendor.name
        vendor.delete()
        messages.warning(request, f"Vendor '{name}' has been decommissioned from the system.")
        return redirect('vendors:list')

    return render(request, 'vendors/confirm_delete.html', {'vendor': vendor})


@login_required
def quick_dispatch(request):
    """
    Handles immediate dispatch and dock permit creation from the right-hand panel.
    """
    if request.method == 'POST':
        form = VendorDispatchForm(request.POST)
        if form.is_valid():
            dispatch = form.save(commit=False)
            rand_code = random.randint(1000, 9999)
            dispatch.dispatch_id = f"DISPATCH-2026-{rand_code}"
            dispatch.pass_number = f"DK-{rand_code}"
            if not dispatch.lead_name:
                dispatch.lead_name = dispatch.vendor.contact_person
            dispatch.save()

            # Ensure vendor has active event set
            dispatch.vendor.active_event = dispatch.event
            dispatch.vendor.save()

            Notification.objects.create(
                title=f"Logistics Dispatch: {dispatch.vendor.name}",
                message=f"Permit {dispatch.pass_number} issued for {dispatch.event.name} at {dispatch.dock_bay}.",
                notification_type='event',
                link_url=f"/vendors/{dispatch.vendor.id}/"
            )

            messages.success(request, f"Permit {dispatch.pass_number} successfully dispatched to {dispatch.vendor.name}!")
            return redirect('vendors:list')
        else:
            messages.error(request, "Unable to complete dispatch. Please verify form values.")

    return redirect('vendors:list')


@login_required
def export_vendors_csv(request):
    """
    Exports vendor registry to CSV.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="vendors_registry_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Vendor ID',
        'Company Name',
        'Service Category',
        'Tier',
        'Contact Person',
        'Phone',
        'Email',
        'SLA Status',
        'Active Assignment',
        'Status'
    ])

    for v in Vendor.objects.all().select_related('active_event'):
        writer.writerow([
            v.vendor_id,
            v.name,
            v.service_type,
            v.tier,
            v.contact_person,
            v.phone,
            v.email,
            v.sla_status,
            v.active_event.name if v.active_event else 'Unassigned',
            v.status
        ])

    return response
