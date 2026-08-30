from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from .models import StaffMember, ResidentStaffAssignment
from .forms import StaffMemberForm, ResidentStaffAssignmentForm
from .forms import StaffMemberForm
from .models import StaffMember


@login_required
@permission_required(
    "staff.view_staffmember",
    raise_exception=True,
)
def staff_list(request):

    staff = StaffMember.objects.select_related(
        "user",
        "facility",
        "ward",
    ).all()

    query = request.GET.get("q", "").strip()

    if query:
        staff = staff.filter(
            Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(user__email__icontains=query)
            | Q(employee_id__icontains=query)
        )

    status = request.GET.get("status")

    if status:
        staff = staff.filter(
            employment_status=status
        )

    staff = staff.order_by(
        "user__last_name",
        "user__first_name",
    )

    return render(
        request,
        "staff/list.html",
        {
            "staff": staff,
            "query": query,
            "status": status,
        },
    )


@login_required
@permission_required(
    "staff.add_staffmember",
    raise_exception=True,
)
def staff_create(request):

    if request.method == "POST":

        form = StaffMemberForm(request.POST)

        if form.is_valid():

            staff_member = form.save()

            messages.success(
                request,
                "Staff member created successfully.",
            )

            return redirect(
                "staff_detail",
                pk=staff_member.pk,
            )

    else:

        form = StaffMemberForm()

    return render(
        request,
        "staff/form.html",
        {
            "form": form,
            "title": "Add Staff Member",
            "button_text": "Create Staff Member",
        },
    )


@login_required
@permission_required(
    "staff.view_staffmember",
    raise_exception=True,
)
def staff_detail(request, pk):

    staff_member = get_object_or_404(
        StaffMember.objects.select_related(
            "user",
            "facility",
            "ward",
        ),
        pk=pk,
    )

    return render(
        request,
        "staff/detail.html",
        {
            "staff_member": staff_member,
        },
    )


@login_required
@permission_required(
    "staff.change_staffmember",
    raise_exception=True,
)
def staff_edit(request, pk):

    staff_member = get_object_or_404(
        StaffMember,
        pk=pk,
    )

    if request.method == "POST":

        form = StaffMemberForm(
            request.POST,
            instance=staff_member,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Staff member updated successfully.",
            )

            return redirect(
                "staff_detail",
                pk=staff_member.pk,
            )

    else:

        form = StaffMemberForm(
            instance=staff_member,
        )

    return render(
        request,
        "staff/form.html",
        {
            "form": form,
            "staff_member": staff_member,
            "title": "Edit Staff Member",
            "button_text": "Save Changes",
        },
    )


@login_required
@permission_required(
    "staff.delete_staffmember",
    raise_exception=True,
)
def staff_delete(request, pk):

    staff_member = get_object_or_404(
        StaffMember,
        pk=pk,
    )

    if request.method == "POST":

        staff_member.delete()

        messages.success(
            request,
            "Staff member deleted successfully.",
        )

        return redirect("staff_list")

    return render(
        request,
        "staff/delete.html",
        {
            "staff_member": staff_member,
        },
    )

@login_required
@permission_required(
    "staff.view_residentstaffassignment",
    raise_exception=True,
)
def assignment_list(request):

    assignments = (
        ResidentStaffAssignment.objects
        .select_related(
            "staff",
            "staff__user",
            "resident",
        )
        .order_by(
            "-is_active",
            "resident__last_name",
        )
    )

    query = request.GET.get("q", "").strip()

    if query:

        assignments = assignments.filter(
            Q(
                resident__first_name__icontains=query
            )
            |
            Q(
                resident__last_name__icontains=query
            )
            |
            Q(
                staff__user__first_name__icontains=query
            )
            |
            Q(
                staff__user__last_name__icontains=query
            )
        )

    return render(
        request,
        "staff/assignment_list.html",
        {
            "assignments": assignments,
            "query": query,
        },
    )
@login_required
@permission_required(
    "staff.add_residentstaffassignment",
    raise_exception=True,
)
def assignment_create(request):

    resident_id = request.GET.get("resident")
    staff_id = request.GET.get("staff")

    initial = {}

    if resident_id:
        initial["resident"] = resident_id

    if staff_id:
        initial["staff"] = staff_id

    if request.method == "POST":

        form = ResidentStaffAssignmentForm(
            request.POST
        )

        if form.is_valid():

            assignment = form.save()

            messages.success(
                request,
                "Staff assignment created successfully.",
            )

            return redirect(
                "assignment_detail",
                pk=assignment.pk,
            )

    else:

        form = ResidentStaffAssignmentForm(
            initial=initial
        )

    return render(
        request,
        "staff/assignment_form.html",
        {
            "form": form,
            "title": "Assign Staff to Resident",
            "button_text": "Create Assignment",
        },
    )
    
@login_required
@permission_required(
    "staff.view_residentstaffassignment",
    raise_exception=True,
)
def assignment_detail(request, pk):

    assignment = get_object_or_404(
        ResidentStaffAssignment.objects.select_related(
            "staff",
            "staff__user",
            "resident",
        ),
        pk=pk,
    )

    return render(
        request,
        "staff/assignment_detail.html",
        {
            "assignment": assignment,
        },
    )
@login_required
@permission_required(
    "staff.change_residentstaffassignment",
    raise_exception=True,
)
def assignment_edit(request, pk):

    assignment = get_object_or_404(
        ResidentStaffAssignment,
        pk=pk,
    )

    if request.method == "POST":

        form = ResidentStaffAssignmentForm(
            request.POST,
            instance=assignment,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Staff assignment updated.",
            )

            return redirect(
                "assignment_detail",
                pk=assignment.pk,
            )

    else:

        form = ResidentStaffAssignmentForm(
            instance=assignment
        )

    return render(
        request,
        "staff/assignment_form.html",
        {
            "form": form,
            "assignment": assignment,
            "title": "Edit Staff Assignment",
            "button_text": "Save Changes",
        },
    )
    
@login_required
@permission_required(
    "staff.delete_residentstaffassignment",
    raise_exception=True,
)
def assignment_delete(request, pk):

    assignment = get_object_or_404(
        ResidentStaffAssignment,
        pk=pk,
    )

    if request.method == "POST":

        assignment.delete()

        messages.success(
            request,
            "Staff assignment deleted.",
        )

        return redirect(
            "assignment_list"
        )

    return render(
        request,
        "staff/assignment_delete.html",
        {
            "assignment": assignment,
        },
    )

from datetime import date

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from .models import StaffMember
from care.models import CareTask
from medications.models import MedicationAdministration
from appointments.models import Appointment
from incidents.models import Incident

@login_required
def staff_workspace(request):
    staff = get_object_or_404(StaffMember,user=request.user)
    today = date.today()
    # -------------------------
    # CARE TASKS
    # -------------------------
    my_tasks = (CareTask.objects.filter(assigned_to=staff,status__in=["pending", "in_progress"]).select_related("resident").order_by("due_date", "due_time"))
    todays_tasks = my_tasks.filter(due_date=today)
    overdue_tasks = my_tasks.filter(due_date__lt=today)
    # -------------------------
    # MEDICATIONS
    # -------------------------
    todays_medications = (
        MedicationAdministration.objects
        .filter(
            administered_by=staff,
            administered_at__date=today,
        )
        .select_related(
            "medication",
            "medication__resident",
        )
        .order_by("-administered_at")
    )


    # -------------------------
    # APPOINTMENTS
    # -------------------------

    todays_appointments = (
        Appointment.objects
        .filter(
            appointment_date=today,
        )
        .select_related("resident")
        .order_by("appointment_time")
    )


    # -------------------------
    # INCIDENTS
    # -------------------------

    open_incidents = (
        Incident.objects
        .filter(
            status__in=["open", "investigating"],
        )
        .select_related(
            "resident",
            "reported_by",
        )
        .order_by("-incident_date")
    )


    context = {
        "staff": staff,
        "today": today,

        "my_tasks": my_tasks,
        "todays_tasks": todays_tasks,
        "overdue_tasks": overdue_tasks,

        "todays_medications": todays_medications,

        "todays_appointments": todays_appointments,

        "open_incidents": open_incidents,
    }

    return render(
        request,
        "staff/workspace.html",
        context,
    )