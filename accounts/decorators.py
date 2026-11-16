from functools import wraps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied


def role_required(allowed_roles):
    """
    Decorator to ensure user is logged in and belongs to one of the allowed roles.
    If the user attempts to access another role's dashboard by typing its URL,
    they are blocked and redirected to their designated dashboard with an alert message.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f"/login/?next={request.path}")

            # Superusers have administrative access across dashboards
            if request.user.is_superuser or request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)

            # Prevent unauthorized cross-role dashboard URL tampering
            role_label = allowed_roles[0].capitalize() if allowed_roles else "designated"
            messages.warning(
                request,
                f"Access Denied: You do not have permission to access the {role_label} area. "
                f"You have been redirected to your authorized dashboard."
            )
            return redirect(request.user.get_dashboard_url())

        return _wrapped_view
    return decorator


def student_required(view_func):
    """Restricts access to IT Student users only."""
    return role_required(['student'])(view_func)


def custodian_required(view_func):
    """Restricts access to Laboratory Custodian / Staff users only."""
    return role_required(['custodian'])(view_func)
