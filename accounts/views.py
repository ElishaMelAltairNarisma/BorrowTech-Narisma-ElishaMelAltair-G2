from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.utils.http import url_has_allowed_host_and_scheme

from .models import User
from .forms import (
    BorrowTechRegistrationForm,
    BorrowTechLoginForm,
    UserProfileUpdateForm,
)
from .decorators import student_required, custodian_required


def home_view(request):
    """Public landing page showcasing BorrowTech platform."""
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')
    return render(request, 'accounts/home.html')


def register_view(request):
    """
    Account Registration:
    - Validates required fields, email format, unique username/email, password confirmation.
    - Hashes password using Django's built-in authentication.
    - Shows clear success or error messages.
    """
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
            # Log in automatically upon registration
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
    """
    User Login:
    - Allows logging in with either Username or Email.
    - Validates credentials and shows error messages on failure.
    - Redirects authenticated user to their role-specific dashboard.
    """
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        form = BorrowTechLoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data.get('username_or_email').strip()
            password = form.cleaned_data.get('password')

            # Find user by username or email
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
    """
    User Logout:
    - Ends user session and redirects to login with confirmation.
    """
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
    - Equipment availability overview
    - Student reservation requests & borrowing history
    - Lab safety & borrowing policies
    - Strict URL protection preventing custodian access
    """
    # Sample hardware inventory data for university IT laboratory
    featured_equipment = [
        {
            'name': 'Arduino Uno R3 Starter Kit',
            'category': 'Embedded Systems & IoT',
            'code': 'EQ-ARD-010',
            'available': 12,
            'total': 15,
            'status': 'Available',
            'badge_color': 'emerald',
        },
        {
            'name': 'Raspberry Pi 4 Model B (8GB RAM)',
            'category': 'Single Board Computers',
            'code': 'EQ-RPI-024',
            'available': 4,
            'total': 8,
            'status': 'Limited',
            'badge_color': 'amber',
        },
        {
            'name': 'Fluke 87V Industrial Multimeter',
            'category': 'Testing & Measurement',
            'code': 'EQ-FLK-003',
            'available': 6,
            'total': 6,
            'status': 'Available',
            'badge_color': 'emerald',
        },
        {
            'name': 'Cisco Catalyst 2960-X Switch',
            'category': 'Networking Laboratory',
            'code': 'EQ-NET-015',
            'available': 0,
            'total': 4,
            'status': 'Reserved / Checked Out',
            'badge_color': 'red',
        },
        {
            'name': 'Rigol DS1054Z Digital Oscilloscope',
            'category': 'Signal Analysis',
            'code': 'EQ-OSC-007',
            'available': 3,
            'total': 5,
            'status': 'Available',
            'badge_color': 'emerald',
        },
    ]

    active_reservations = [
        {
            'id': 'RES-2026-089',
            'item': 'Raspberry Pi 4 Model B (8GB)',
            'date': 'Today at 09:30 AM',
            'due_date': 'Tomorrow at 05:00 PM',
            'status': 'Active Loan',
            'status_color': 'emerald',
        },
        {
            'id': 'RES-2026-092',
            'item': 'Fluke 87V Multimeter',
            'date': 'Today at 01:15 PM',
            'due_date': 'Awaiting Custodian Approval',
            'status': 'Pending Approval',
            'status_color': 'amber',
        },
    ]

    context = {
        'role_title': 'IT Student Dashboard',
        'equipment_list': featured_equipment,
        'active_reservations': active_reservations,
    }
    return render(request, 'accounts/student_dashboard.html', context)


@custodian_required
def custodian_dashboard_view(request):
    """
    Role-Based Dashboard for Laboratory Custodians:
    - Equipment inventory summary and audit trail
    - Pending reservation approvals queue
    - Overdue returns tracking & alert notifications
    - Strict URL protection preventing student access
    """
    stats = {
        'total_inventory': 148,
        'available_items': 112,
        'active_loans': 26,
        'pending_approvals': 7,
        'overdue_returns': 3,
    }

    pending_queue = [
        {
            'req_id': 'REQ-2026-104',
            'student_name': 'Juan Dela Cruz',
            'student_id': '2024-IT-0142',
            'equipment': 'Cisco 2960-X Switch (EQ-NET-015)',
            'purpose': 'CCNA Laboratory Practical Exam #2',
            'requested_at': '10 mins ago',
            'duration': '4 Hours',
        },
        {
            'req_id': 'REQ-2026-105',
            'student_name': 'Maria Santos',
            'student_id': '2023-CS-0091',
            'equipment': 'Rigol Oscilloscope (EQ-OSC-007)',
            'purpose': 'Capstone Hardware Circuit Testing',
            'requested_at': '25 mins ago',
            'duration': '2 Days',
        },
        {
            'req_id': 'REQ-2026-106',
            'student_name': 'Carlos Reyes',
            'student_id': '2024-IT-0318',
            'equipment': 'Arduino Starter Kit (EQ-ARD-010)',
            'purpose': 'Embedded Systems Lab Session',
            'requested_at': '1 hour ago',
            'duration': '3 Hours',
        },
    ]

    recent_audit_trail = [
        {
            'timestamp': 'Today 01:45 PM',
            'custodian': request.user.get_full_name() or request.user.username,
            'action': 'Approved Loan RES-2026-089',
            'details': 'Issued Raspberry Pi 4 to Student 2024-IT-0142',
        },
        {
            'timestamp': 'Today 11:15 AM',
            'custodian': request.user.get_full_name() or request.user.username,
            'action': 'Returned Item EQ-FLK-001',
            'details': 'Returned Fluke Multimeter inspected & marked Operational',
        },
        {
            'timestamp': 'Today 08:30 AM',
            'custodian': 'System Audit',
            'action': 'Overdue Notification Sent',
            'details': 'Sent reminder to 2023-IT-0842 for late soldering station',
        },
    ]

    context = {
        'role_title': 'Laboratory Custodian Management Console',
        'stats': stats,
        'pending_queue': pending_queue,
        'audit_trail': recent_audit_trail,
    }
    return render(request, 'accounts/custodian_dashboard.html', context)


@login_required
def profile_view(request):
    """
    User Profile Management:
    - Logged-in users can view their profile information.
    - Users can update their profile details (name, email, contact, department, year, profile photo).
    - Strict boundary: Users can ONLY view and edit their OWN profile (instance=request.user).
    """
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
            # Prevent the user from being logged out when their password changes
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was successfully updated!")
            return redirect('profile')
        else:
            messages.error(request, "Please correct the errors below to change your password.")
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'accounts/change_password.html', {'form': form})
