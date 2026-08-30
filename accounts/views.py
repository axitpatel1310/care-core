from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .forms import UserRoleForm
from .models import User
from .models import User
from .audit import create_audit_log

def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=email,
            password=password,
        )

        if user is not None:
            login(request, user)

            next_url = request.GET.get("next")

            if next_url:
                return redirect(next_url)

            return redirect("dashboard")

        messages.error(
            request,
            "Invalid email or password."
        )

    return render(request, "accounts/login.html")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        role = "care_worker"
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

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

        elif User.objects.filter(email=email).exists():
            messages.error(
                request,
                "An account with this email already exists."
            )

        elif password != confirm_password:
            messages.error(
                request,
                "Passwords do not match."
            )

        elif len(password) < 8:
            messages.error(
                request,
                "Password must contain at least 8 characters."
            )

        else:
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role=role,
            )

            messages.success(
                request,
                "Account created successfully. You can now sign in."
            )

            return redirect("login")

    return render(request, "accounts/register.html")


@login_required
def logout_view(request):
    logout(request)

    return redirect("login")

@login_required
def user_management(request):

    if request.user.role != "admin":
        return redirect("dashboard")

    users = User.objects.all().order_by(
        "last_name",
        "first_name",
    )

    return render(
        request,
        "accounts/user_management.html",
        {
            "users": users,
        },
    )
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

from .models import AuditLog
@login_required
def audit_log(request):

    if request.user.role != "admin":
        return redirect("dashboard")

    logs = (
        AuditLog.objects
        .select_related("user")
        .order_by("-timestamp")
    )

    return render(
        request,
        "accounts/audit_log.html",
        {
            "logs": logs,
        },
    )