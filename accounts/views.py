from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.db.models import Sum

from .models import User
from .forms import (
    BorrowTechRegistrationForm,
    BorrowTechLoginForm,
    UserProfileUpdateForm,
)
from .decorators import student_required, custodian_required
from equipment.models import Equipment
from reservations.models import BorrowReservation


def home_view(request):
    """Public landing page showcasing BorrowTech platform."""
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')
    featured_equipment = Equipment.objects.filter(is_active=True).select_related('category')[:4]
    return render(request, 'accounts/home.html', {'featured_equipment': featured_equipment})


def register_view(request):
    """Account Registration with input validation, role selection, and hashed passwords."""
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        form = BorrowTechRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f"Account created successfully for {user.get_full_name() or user.username}! "
                f"You have been registered as an {user.get_role_display()}."
            )
            login(request, user)
            return redirect(user.get_dashboard_url())
        else:
            messages.error(
                request,
                "Registration failed. Please correct the highlighted errors below."
            )
    else:
        form = BorrowTechRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """Login view supporting Username or Email with error feedback."""
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        form = BorrowTechLoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data.get('username_or_email').strip()
            password = form.cleaned_data.get('password')

            user_obj = None
            if '@' in username_or_email:
                user_obj = User.objects.filter(email__iexact=username_or_email).first()
            if not user_obj:
                user_obj = User.objects.filter(username__iexact=username_or_email).first()

            user = None
            if user_obj:
                user = authenticate(request, username=user_obj.username, password=password)

            if user is not None:
                login(request, user)
                messages.success(
                    request,
                    f"Welcome back, {user.get_full_name() or user.username}! "
                    f"Logged in as {user.get_role_display()}."
                )
                next_url = request.GET.get('next')
                if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                    return redirect(next_url)
                return redirect(user.get_dashboard_url())
            else:
                messages.error(
                    request,
                    "Invalid username/email or password. Please verify your credentials and try again."
                )
        else:
            messages.error(request, "Please fill in all required login fields.")
    else:
        form = BorrowTechLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """Logs out user, clears session, and redirects to login."""
    user_name = request.user.get_full_name() or request.user.username
    logout(request)
    messages.info(request, f"Goodbye, {user_name}. You have been safely logged out of BorrowTech.")
    return redirect('login')


@login_required
def dashboard_redirect_view(request):
    """Directs logged-in users directly to their designated role dashboard."""
    return redirect(request.user.get_dashboard_url())


@student_required
def student_dashboard_view(request):
    """
    Role-Based Dashboard for IT Students:
    - Real-time hardware equipment availability from database.
    - User's actual reservations and digital loans.
    - Concurrent quota tracking (Max 3 items).
    """
    my_reservations = BorrowReservation.objects.filter(
        borrower=request.user
    ).select_related('equipment').order_by('-created_at')[:5]

    active_loans_count = BorrowReservation.objects.filter(
        borrower=request.user,
        status=BorrowReservation.Status.ISSUED
    ).count()

    pending_count = BorrowReservation.objects.filter(
        borrower=request.user,
        status=BorrowReservation.Status.PENDING
    ).count()

    approved_count = BorrowReservation.objects.filter(
        borrower=request.user,
        status=BorrowReservation.Status.APPROVED
    ).count()

    quota_used = active_loans_count + pending_count + approved_count
    quota_left = max(0, 3 - quota_used)

    equipment_list = Equipment.objects.filter(is_active=True).select_related('category')[:6]

    context = {
        'role_title': 'IT Student Dashboard',
        'equipment_list': equipment_list,
        'active_reservations': my_reservations,
        'active_loans_count': active_loans_count,
        'pending_count': pending_count,
        'quota_left': quota_left,
    }
    return render(request, 'accounts/student_dashboard.html', context)


@custodian_required
def custodian_dashboard_view(request):
    """
    Role-Based Dashboard for Laboratory Custodians:
    - Live inventory totals, active loans, and overdue counts.
    - Pending student reservation queue with quick actions.
    - Real laboratory return inspection audit log.
    """
    total_inventory = Equipment.objects.aggregate(Sum('total_quantity'))['total_quantity__sum'] or 0
    available_items = Equipment.objects.aggregate(Sum('available_quantity'))['available_quantity__sum'] or 0
    active_loans = BorrowReservation.objects.filter(status=BorrowReservation.Status.ISSUED).count()
    pending_approvals = BorrowReservation.objects.filter(status=BorrowReservation.Status.PENDING).count()
    overdue_returns = BorrowReservation.objects.filter(
        status=BorrowReservation.Status.ISSUED,
        expected_return_date__lt=timezone.now().date()
    ).count()

    stats = {
        'total_inventory': total_inventory,
        'available_items': available_items,
        'active_loans': active_loans,
        'pending_approvals': pending_approvals,
        'overdue_returns': overdue_returns,
    }

    pending_queue = BorrowReservation.objects.filter(
        status=BorrowReservation.Status.PENDING
    ).select_related('equipment', 'borrower').order_by('-created_at')[:5]

    recent_audit = BorrowReservation.objects.filter(
        status__in=[BorrowReservation.Status.RETURNED, BorrowReservation.Status.ISSUED]
    ).select_related('equipment', 'borrower', 'inspected_by').order_by('-updated_at')[:5]

    context = {
        'role_title': 'Laboratory Custodian Management Console',
        'stats': stats,
        'pending_queue': pending_queue,
        'audit_trail': recent_audit,
    }
    return render(request, 'accounts/custodian_dashboard.html', context)


@login_required
def profile_view(request):
    """User Profile: Users can view and edit ONLY their own profile."""
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile details have been successfully updated.")
            return redirect('profile')
        else:
            messages.error(request, "Failed to update profile. Please review the errors below.")
    else:
        form = UserProfileUpdateForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def change_password_view(request):
    """Allows logged-in users to securely change their password."""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was successfully updated!")
            return redirect('profile')
        else:
            messages.error(request, "Please correct the errors below to change your password.")
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'accounts/change_password.html', {'form': form})
