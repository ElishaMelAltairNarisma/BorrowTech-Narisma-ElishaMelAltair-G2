from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.db import transaction

from accounts.decorators import custodian_required
from equipment.models import Equipment
from .models import BorrowReservation
from .forms import (
    BorrowReservationCreateForm,
    BorrowReservationUpdateForm,
    CustodianReturnForm,
    CustodianRejectForm
)


@login_required
def reservation_create_view(request):
    """
    Create Reservation (Create operation):
    - Logged-in students can submit a digital equipment reservation request.
    - Enforces business rules: stock limits, maximum 7-day loan, max 3 active requests.
    """
    initial_data = {}
    equipment_id = request.GET.get('equipment')
    if equipment_id:
        equipment = get_object_or_404(Equipment, pk=equipment_id, is_active=True)
        initial_data['equipment'] = equipment

    if request.method == 'POST':
        form = BorrowReservationCreateForm(request.POST, user=request.user)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.borrower = request.user
            reservation.status = BorrowReservation.Status.PENDING
            reservation.save()
            messages.success(
                request,
                f"Reservation {reservation.reservation_code} for '{reservation.equipment.name}' "
                f"submitted successfully. Awaiting Lab Custodian approval."
            )
            return redirect('reservation_detail', pk=reservation.pk)
        else:
            messages.error(request, "Failed to submit reservation. Please correct the highlighted errors.")
    else:
        form = BorrowReservationCreateForm(initial=initial_data, user=request.user)

    return render(request, 'reservations/reservation_create.html', {'form': form})


@login_required
def my_reservations_view(request):
    """
    Student Reservations List (Read operation):
    - Users can ONLY view their own reservation records (linked via ForeignKey).
    - Filterable by reservation status.
    """
    status_filter = request.GET.get('status', 'all')
    reservations_qs = BorrowReservation.objects.filter(borrower=request.user).select_related('equipment', 'borrower')

    if status_filter == 'pending':
        reservations_qs = reservations_qs.filter(status=BorrowReservation.Status.PENDING)
    elif status_filter == 'active':
        reservations_qs = reservations_qs.filter(status__in=[BorrowReservation.Status.APPROVED, BorrowReservation.Status.ISSUED])
    elif status_filter == 'completed':
        reservations_qs = reservations_qs.filter(status=BorrowReservation.Status.RETURNED)
    elif status_filter == 'archived':
        reservations_qs = reservations_qs.filter(status__in=[BorrowReservation.Status.REJECTED, BorrowReservation.Status.CANCELLED])

    context = {
        'reservations': reservations_qs,
        'current_filter': status_filter,
        'total_count': reservations_qs.count(),
    }
    return render(request, 'reservations/my_reservations.html', context)


@login_required
def reservation_detail_view(request, pk):
    """
    Reservation Detail / Digital Pass (Read operation):
    - Displays full reservation details, timestamps, and return inspection notes.
    - Security: Students can only view their own; Custodians can view all.
    """
    reservation = get_object_or_404(
        BorrowReservation.objects.select_related('equipment', 'borrower', 'inspected_by'),
        pk=pk
    )

    # Permission check: own record or custodian/superuser
    if reservation.borrower != request.user and not request.user.is_custodian_user() and not request.user.is_superuser:
        messages.error(request, "Access denied: You do not have permission to view another student's reservation.")
        return redirect('my_reservations')

    context = {
        'reservation': reservation,
    }
    return render(request, 'reservations/reservation_detail.html', context)


@login_required
def reservation_update_view(request, pk):
    """
    Reservation Modification (Update operation):
    - Students can only update their own pending reservations.
    """
    reservation = get_object_or_404(BorrowReservation, pk=pk)

    if reservation.borrower != request.user:
        messages.error(request, "Permission denied: You can only edit your own reservations.")
        return redirect('my_reservations')

    if not reservation.can_edit:
        messages.warning(
            request,
            f"Reservation {reservation.reservation_code} cannot be edited because it is already {reservation.get_status_display()}."
        )
        return redirect('reservation_detail', pk=reservation.pk)

    if request.method == 'POST':
        form = BorrowReservationUpdateForm(request.POST, instance=reservation)
        if form.is_valid():
            form.save()
            messages.success(request, f"Reservation {reservation.reservation_code} updated successfully.")
            return redirect('reservation_detail', pk=reservation.pk)
        else:
            messages.error(request, "Failed to update reservation. Please review the errors below.")
    else:
        form = BorrowReservationUpdateForm(instance=reservation)

    return render(request, 'reservations/reservation_update.html', {
        'form': form,
        'reservation': reservation
    })


@login_required
def reservation_cancel_view(request, pk):
    """
    Reservation Cancellation (Delete operation):
    - Students can cancel their own pending or approved reservations.
    """
    reservation = get_object_or_404(BorrowReservation, pk=pk)

    if reservation.borrower != request.user:
        messages.error(request, "Permission denied: You can only cancel your own reservations.")
        return redirect('my_reservations')

    if not reservation.can_cancel:
        messages.warning(
            request,
            f"Reservation {reservation.reservation_code} cannot be cancelled in its current state."
        )
        return redirect('reservation_detail', pk=reservation.pk)

    if request.method == 'POST':
        reservation.status = BorrowReservation.Status.CANCELLED
        reservation.save()
        messages.success(request, f"Reservation {reservation.reservation_code} has been cancelled.")
        return redirect('my_reservations')

    return render(request, 'reservations/reservation_confirm_cancel.html', {'reservation': reservation})


# ==============================================================================
# LABORATORY CUSTODIAN WORKFLOW & APPROVALS
# ==============================================================================

@custodian_required
def custodian_queue_view(request):
    """
    Custodian Queue (Read operation):
    - Custodian console listing all laboratory equipment loan requests.
    - Status tabs for Pending, Active Loans, Overdue items, and Returned history.
    """
    status_tab = request.GET.get('tab', 'pending')
    all_qs = BorrowReservation.objects.select_related('equipment', 'borrower').order_by('-created_at')

    if status_tab == 'pending':
        items = all_qs.filter(status=BorrowReservation.Status.PENDING)
    elif status_tab == 'approved':
        items = all_qs.filter(status=BorrowReservation.Status.APPROVED)
    elif status_tab == 'active':
        items = all_qs.filter(status=BorrowReservation.Status.ISSUED)
    elif status_tab == 'overdue':
        today = timezone.now().date()
        items = all_qs.filter(status=BorrowReservation.Status.ISSUED, expected_return_date__lt=today)
    elif status_tab == 'returned':
        items = all_qs.filter(status=BorrowReservation.Status.RETURNED)
    else:
        items = all_qs

    pending_count = all_qs.filter(status=BorrowReservation.Status.PENDING).count()
    active_count = all_qs.filter(status=BorrowReservation.Status.ISSUED).count()
    approved_count = all_qs.filter(status=BorrowReservation.Status.APPROVED).count()
    overdue_count = all_qs.filter(status=BorrowReservation.Status.ISSUED, expected_return_date__lt=timezone.now().date()).count()

    context = {
        'items': items,
        'current_tab': status_tab,
        'pending_count': pending_count,
        'active_count': active_count,
        'approved_count': approved_count,
        'overdue_count': overdue_count,
    }
    return render(request, 'reservations/custodian_queue.html', context)


@custodian_required
def custodian_approve_view(request, pk):
    """Custodian approves a pending reservation request."""
    reservation = get_object_or_404(BorrowReservation, pk=pk)

    if reservation.status != BorrowReservation.Status.PENDING:
        messages.warning(request, f"Reservation {reservation.reservation_code} is not in pending status.")
        return redirect('custodian_queue')

    reservation.status = BorrowReservation.Status.APPROVED
    reservation.save()
    messages.success(
        request,
        f"Reservation {reservation.reservation_code} for {reservation.borrower.get_full_name() or reservation.borrower.username} has been APPROVED."
    )
    return redirect('custodian_queue')


@custodian_required
def custodian_reject_view(request, pk):
    """Custodian rejects a reservation request with mandatory remarks."""
    reservation = get_object_or_404(BorrowReservation, pk=pk)

    if request.method == 'POST':
        form = CustodianRejectForm(request.POST)
        if form.is_valid():
            reservation.status = BorrowReservation.Status.REJECTED
            reservation.custodian_remarks = form.cleaned_data['custodian_remarks']
            reservation.save()
            messages.info(
                request,
                f"Reservation {reservation.reservation_code} was REJECTED with notes recorded."
            )
            return redirect('custodian_queue')
    else:
        form = CustodianRejectForm()

    return render(request, 'reservations/custodian_reject.html', {
        'form': form,
        'reservation': reservation
    })


@custodian_required
def custodian_issue_view(request, pk):
    """
    Hardware Handover (Status -> ISSUED):
    - Custodian physically hands over equipment to the student.
    - Atomically decrements equipment available_quantity.
    """
    reservation = get_object_or_404(BorrowReservation.objects.select_related('equipment'), pk=pk)

    if reservation.status != BorrowReservation.Status.APPROVED:
        messages.warning(request, "Only approved reservations can be issued for loan.")
        return redirect('custodian_queue')

    equipment = reservation.equipment
    if equipment.available_quantity < reservation.quantity:
        messages.error(
            request,
            f"Cannot issue: Only {equipment.available_quantity} unit(s) available in stock."
        )
        return redirect('custodian_queue')

    with transaction.atomic():
        equipment.available_quantity -= reservation.quantity
        equipment.save()
        reservation.status = BorrowReservation.Status.ISSUED
        reservation.save()

    messages.success(
        request,
        f"Equipment successfully ISSUED to {reservation.borrower.get_full_name() or reservation.borrower.username}! "
        f"Stock updated ({equipment.available_quantity} remaining)."
    )
    return redirect('custodian_queue')


@custodian_required
def custodian_return_view(request, pk):
    """
    Return Processing & Inspection (Status -> RETURNED):
    - Student returns hardware to laboratory counter.
    - Custodian inspects condition and records audit notes.
    - Atomically increments equipment available_quantity.
    """
    reservation = get_object_or_404(BorrowReservation.objects.select_related('equipment'), pk=pk)

    if reservation.status != BorrowReservation.Status.ISSUED:
        messages.warning(request, "Only currently issued active loans can be returned.")
        return redirect('custodian_queue')

    if request.method == 'POST':
        form = CustodianReturnForm(request.POST)
        if form.is_valid():
            condition = form.cleaned_data['return_condition']
            remarks = form.cleaned_data['custodian_remarks']

            with transaction.atomic():
                equipment = reservation.equipment
                equipment.available_quantity += reservation.quantity
                if condition == BorrowReservation.Condition.DAMAGED:
                    equipment.condition = Equipment.Condition.NEEDS_MAINTENANCE
                equipment.save()

                reservation.status = BorrowReservation.Status.RETURNED
                reservation.return_condition = condition
                reservation.custodian_remarks = remarks
                reservation.inspected_by = request.user
                reservation.actual_return_date = timezone.now()
                reservation.save()

            messages.success(
                request,
                f"Equipment returned successfully. Condition recorded: '{reservation.get_return_condition_display()}'. "
                f"Inventory restored ({equipment.available_quantity} available)."
            )
            return redirect('custodian_queue')
    else:
        form = CustodianReturnForm()

    return render(request, 'reservations/custodian_return.html', {
        'form': form,
        'reservation': reservation
    })
