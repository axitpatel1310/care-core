from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from . import throttle
from .audit import create_audit_log
from .audit_trail import client_ip
from .forms import UserRoleForm
from .models import AuditLog, User


def safe_next_url(request):
    """Only follow ?next= when it points back into this site (prevents open redirects)."""

    next_url = request.POST.get("next") or request.GET.get("next")

    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url

    return None


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    email = ""

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        ip = client_ip(request)

        if throttle.is_locked(email, ip):
            create_audit_log(
                user=None,
                action="login_failed",
                module="accounts",
                description=f"Sign-in blocked by throttling for '{email}'.",
                ip_address=ip,
            )

            messages.error(
                request,
                "Too many failed sign-in attempts. Please wait "
                f"{throttle.lockout_minutes()} minutes and try again.",
            )

            return render(request, "accounts/login.html", {"email": email}, status=429)

        # authenticate() fires the signals that write the sign-in audit entries.
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            throttle.register_success(email, ip)

            return redirect(safe_next_url(request) or "dashboard")

        throttle.register_failure(email, ip)

        pending = User.objects.filter(email__iexact=email, is_active=False).first()

        if pending and pending.check_password(password):
            messages.info(
                request,
                "Your account is awaiting approval by an administrator.",
            )
        else:
            messages.error(
                request,
                "Invalid email or password."
            )

    return render(
        request,
        "accounts/login.html",
        {
            "email": email,
            "next": safe_next_url(request) or "",
        },
    )


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        candidate = User(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )

        try:
            validate_password(password, user=candidate)
            password_error = None
        except ValidationError as error:
            password_error = " ".join(error.messages)

        if not first_name or not last_name:
            messages.error(
                request,
                "Please enter your full name."
            )

        elif not email:
            messages.error(
                request,
                "Please enter an email address."
            )

        elif User.objects.filter(email__iexact=email).exists():
            messages.error(
                request,
                "An account with this email already exists."
            )

        elif password != confirm_password:
            messages.error(
                request,
                "Passwords do not match."
            )

        elif password_error:
            messages.error(
                request,
                password_error,
            )

        else:
            # New accounts cannot see resident data until an administrator approves them.
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role="care_worker",
                is_active=False,
            )

            create_audit_log(
                user=None,
                action="create",
                module="accounts",
                description=f"Account requested by {email}; awaiting approval.",
                object_type="User",
                object_id=user.pk,
                ip_address=client_ip(request),
            )

            messages.success(
                request,
                "Account requested. An administrator must approve it before you can sign in."
            )

            return redirect("login")

    return render(request, "accounts/register.html")


@require_POST
@login_required
def logout_view(request):
    logout(request)

    return redirect("login")


@login_required
def user_management(request):

    if request.user.role != "admin":
        return redirect("dashboard")

    users = User.objects.order_by(
        "last_name",
        "first_name",
    )

    return render(
        request,
        "accounts/user_management.html",
        {
            "pending_users": users.filter(is_active=False, last_login__isnull=True),
            "users": users.exclude(is_active=False, last_login__isnull=True),
        },
    )


@require_POST
@login_required
def user_approve(request, pk):

    if request.user.role != "admin":
        return redirect("dashboard")

    user = get_object_or_404(User, pk=pk, is_active=False)

    role = request.POST.get("role", user.role)

    if role in dict(User.ROLE_CHOICES):
        user.role = role

    user.is_active = True
    user.save()

    create_audit_log(
        user=request.user,
        action="update",
        module="accounts",
        description=f"Approved account for {user.email} as {user.get_role_display()}.",
        object_type="User",
        object_id=user.pk,
        ip_address=client_ip(request),
    )

    messages.success(
        request,
        f"{user.get_full_name() or user.email} can now sign in as {user.get_role_display()}.",
    )

    return redirect("user_management")


@login_required
def user_edit(request, pk):

    if request.user.role != "admin":
        return redirect("dashboard")

    user = get_object_or_404(
        User,
        pk=pk,
    )

    if request.method == "POST":
        form = UserRoleForm(request.POST,instance=user,)
        if form.is_valid():
            old_role = user.role
            updated_user = form.save()
            if old_role != updated_user.role:
                create_audit_log(
                    user=request.user,
                    action="update",
                    module="accounts",
                    description=(
                        f"Changed {updated_user.get_full_name() or updated_user.email} "
                        f"role from {old_role} to {updated_user.role}."
                    ),
                    object_type="User",
                    object_id=updated_user.pk,
                )
            return redirect(
                "user_management"
            )
    else:
        form = UserRoleForm(instance=user)
    return render(
        request,
        "accounts/user_edit.html",
        {
            "form": form,
            "managed_user": user,
        },
    )

@login_required
def audit_log(request):

    if request.user.role != "admin":
        return redirect("dashboard")

    logs = (
        AuditLog.objects
        .select_related("user")
        .order_by("-timestamp")
    )

    action = request.GET.get("action", "")
    module = request.GET.get("module", "")
    query = request.GET.get("q", "").strip()

    if action:
        logs = logs.filter(action=action)

    if module:
        logs = logs.filter(module=module)

    if query:
        logs = logs.filter(
            Q(description__icontains=query)
            | Q(user__email__icontains=query)
            | Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
        )

    page = Paginator(logs, 50).get_page(request.GET.get("page"))

    filters = request.GET.copy()
    filters.pop("page", None)

    return render(
        request,
        "accounts/audit_log.html",
        {
            "logs": page,
            "page": page,
            "action": action,
            "module": module,
            "query": query,
            "filter_query": filters.urlencode(),
            "action_choices": AuditLog.ACTION_CHOICES,
            "modules": (
                AuditLog.objects
                .order_by("module")
                .values_list("module", flat=True)
                .distinct()
            ),
        },
    )
