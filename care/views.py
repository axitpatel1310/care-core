from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from residents.models import Resident,ResidentContact
from .forms import CarePlanForm,AssessmentForm,CognitiveBehaviouralSupportForm
from .models import CarePlan, Assessment

@login_required
@permission_required(
    "care.view_careplan",
    raise_exception=True,
)
def care_plan_list(request):

    care_plans = CarePlan.objects.select_related(
        "resident",
        "responsible_staff",
        "created_by",
    ).all()

    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    if query:

        care_plans = care_plans.filter(
            Q(resident__first_name__icontains=query)
            | Q(resident__last_name__icontains=query)
        )

    if status:

        care_plans = care_plans.filter(
            status=status
        )

    care_plans = care_plans.order_by(
        "-created_at"
    )

    return render(
        request,
        "care/care_plan_list.html",
        {
            "care_plans": care_plans,
            "query": query,
            "status": status,
        },
    )


@login_required
@permission_required(
    "care.add_careplan",
    raise_exception=True,
)
def care_plan_create(request):

    resident_id = request.GET.get("resident")

    initial = {}

    if resident_id:
        resident = get_object_or_404(
            Resident,
            pk=resident_id,
        )

        initial["resident"] = resident

    if request.method == "POST":

        form = CarePlanForm(request.POST)

        if form.is_valid():

            care_plan = form.save(
                commit=False
            )

            care_plan.created_by = request.user

            care_plan.save()

            messages.success(
                request,
                "Care plan created successfully.",
            )

            return redirect(
                "care_plan_detail",
                pk=care_plan.pk,
            )

    else:

        form = CarePlanForm(
            initial=initial
        )

    return render(
        request,
        "care/care_plan_form.html",
        {
            "form": form,
            "title": "Create Care Plan",
            "button_text": "Create Care Plan",
        },
    )

@login_required
@permission_required(
    "care.view_careplan",
    raise_exception=True,
)
def care_plan_detail(request, pk):

    care_plan = get_object_or_404(
        CarePlan.objects.select_related(
            "resident",
            "responsible_staff",
            "created_by",
        ),
        pk=pk,
    )

    return render(
        request,
        "care/care_plan_detail.html",
        {
            "care_plan": care_plan,
        },
    )


@login_required
@permission_required(
    "care.change_careplan",
    raise_exception=True,
)
def care_plan_edit(request, pk):

    care_plan = get_object_or_404(
        CarePlan,
        pk=pk,
    )

    if request.method == "POST":

        form = CarePlanForm(
            request.POST,
            instance=care_plan,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Care plan updated successfully.",
            )

            return redirect(
                "care_plan_detail",
                pk=care_plan.pk,
            )

    else:

        form = CarePlanForm(
            instance=care_plan,
        )

    return render(
        request,
        "care/care_plan_form.html",
        {
            "form": form,
            "care_plan": care_plan,
            "title": "Edit Care Plan",
            "button_text": "Save Changes",
        },
    )


@login_required
@permission_required(
    "care.delete_careplan",
    raise_exception=True,
)
def care_plan_delete(request, pk):

    care_plan = get_object_or_404(
        CarePlan,
        pk=pk,
    )

    if request.method == "POST":

        care_plan.delete()

        messages.success(
            request,
            "Care plan deleted successfully.",
        )

        return redirect(
            "care_plan_list"
        )

    return render(
        request,
        "care/care_plan_delete.html",
        {
            "care_plan": care_plan,
        },
    )
    
@login_required
@permission_required(
    "care.view_assessment",
    raise_exception=True,
)
def assessment_list(request):

    assessments = Assessment.objects.select_related(
        "resident",
        "performed_by",
    ).all()

    query = request.GET.get("q", "").strip()

    if query:

        assessments = assessments.filter(
            Q(
                resident__first_name__icontains=query
            )
            |
            Q(
                resident__last_name__icontains=query
            )
        )

    assessments = assessments.order_by(
        "-assessment_date"
    )

    return render(
        request,
        "care/assessment_list.html",
        {
            "assessments": assessments,
            "query": query,
        },
    )


@login_required
@permission_required(
    "care.add_assessment",
    raise_exception=True,
)
def assessment_create(request):

    resident_id = request.GET.get("resident")

    initial = {}

    if resident_id:

        resident = get_object_or_404(
            Resident,
            pk=resident_id,
        )

        initial["resident"] = resident

    if request.method == "POST":

        form = AssessmentForm(request.POST)

        if form.is_valid():

            assessment = form.save()

            messages.success(
                request,
                "Assessment created successfully.",
            )

            return redirect(
                "assessment_detail",
                pk=assessment.pk,
            )

    else:

        form = AssessmentForm(
            initial=initial
        )

    return render(
        request,
        "care/assessment_form.html",
        {
            "form": form,
            "title": "Create Assessment",
            "button_text": "Create Assessment",
        },
    )


@login_required
@permission_required(
    "care.view_assessment",
    raise_exception=True,
)
def assessment_detail(request, pk):

    assessment = get_object_or_404(
        Assessment.objects.select_related(
            "resident",
            "performed_by",
        ),
        pk=pk,
    )

    return render(
        request,
        "care/assessment_detail.html",
        {
            "assessment": assessment,
        },
    )


@login_required
@permission_required(
    "care.change_assessment",
    raise_exception=True,
)
def assessment_edit(request, pk):

    assessment = get_object_or_404(
        Assessment,
        pk=pk,
    )

    if request.method == "POST":

        form = AssessmentForm(
            request.POST,
            instance=assessment,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Assessment updated successfully.",
            )

            return redirect(
                "assessment_detail",
                pk=assessment.pk,
            )

    else:

        form = AssessmentForm(
            instance=assessment,
        )

    return render(
        request,
        "care/assessment_form.html",
        {
            "form": form,
            "assessment": assessment,
            "title": "Edit Assessment",
            "button_text": "Save Changes",
        },
    )


@login_required
@permission_required(
    "care.delete_assessment",
    raise_exception=True,
)
def assessment_delete(request, pk):

    assessment = get_object_or_404(
        Assessment,
        pk=pk,
    )

    if request.method == "POST":

        assessment.delete()

        messages.success(
            request,
            "Assessment deleted successfully.",
        )

        return redirect(
            "assessment_list"
        )

    return render(
        request,
        "care/assessment_delete.html",
        {
            "assessment": assessment,
        },
    )
    
from .models import (
    CarePlan,
    Assessment,
    CognitiveBehaviouralSupport,
)

@login_required
@permission_required(
    "care.view_cognitivebehaviouralsupport",
    raise_exception=True,
)
def behavioural_support_list(request):

    supports = CognitiveBehaviouralSupport.objects.select_related(
        "resident",
    ).all()

    query = request.GET.get("q", "").strip()

    if query:

        supports = supports.filter(
            Q(
                resident__first_name__icontains=query
            )
            |
            Q(
                resident__last_name__icontains=query
            )
        )

    supports = supports.order_by(
        "resident__last_name",
        "resident__first_name",
    )

    return render(
        request,
        "care/behavioural_support_list.html",
        {
            "supports": supports,
            "query": query,
        },
    )


@login_required
@permission_required(
    "care.add_cognitivebehaviouralsupport",
    raise_exception=True,
)
def behavioural_support_create(request):

    resident_id = request.GET.get("resident")

    initial = {}

    if resident_id:

        resident = get_object_or_404(
            Resident,
            pk=resident_id,
        )

        initial["resident"] = resident

    if request.method == "POST":

        form = CognitiveBehaviouralSupportForm(
            request.POST
        )

        if form.is_valid():

            support = form.save()

            messages.success(
                request,
                "Behavioural support record created successfully.",
            )

            return redirect(
                "behavioural_support_detail",
                pk=support.pk,
            )

    else:

        form = CognitiveBehaviouralSupportForm(
            initial=initial
        )

    return render(
        request,
        "care/behavioural_support_form.html",
        {
            "form": form,
            "title": "Add Cognitive & Behavioural Support",
            "button_text": "Save Support Plan",
        },
    )


@login_required
@permission_required(
    "care.view_cognitivebehaviouralsupport",
    raise_exception=True,
)
def behavioural_support_detail(request, pk):

    support = get_object_or_404(
        CognitiveBehaviouralSupport.objects.select_related(
            "resident",
        ),
        pk=pk,
    )

    return render(
        request,
        "care/behavioural_support_detail.html",
        {
            "support": support,
        },
    )


@login_required
@permission_required(
    "care.change_cognitivebehaviouralsupport",
    raise_exception=True,
)
def behavioural_support_edit(request, pk):

    support = get_object_or_404(
        CognitiveBehaviouralSupport,
        pk=pk,
    )

    if request.method == "POST":

        form = CognitiveBehaviouralSupportForm(
            request.POST,
            instance=support,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Behavioural support record updated successfully.",
            )

            return redirect(
                "behavioural_support_detail",
                pk=support.pk,
            )

    else:

        form = CognitiveBehaviouralSupportForm(
            instance=support,
        )

    return render(
        request,
        "care/behavioural_support_form.html",
        {
            "form": form,
            "support": support,
            "title": "Edit Cognitive & Behavioural Support",
            "button_text": "Save Changes",
        },
    )


@login_required
@permission_required(
    "care.delete_cognitivebehaviouralsupport",
    raise_exception=True,
)
def behavioural_support_delete(request, pk):

    support = get_object_or_404(
        CognitiveBehaviouralSupport,
        pk=pk,
    )

    if request.method == "POST":

        support.delete()

        messages.success(
            request,
            "Behavioural support record deleted successfully.",
        )

        return redirect(
            "behavioural_support_list"
        )

    return render(
        request,
        "care/behavioural_support_delete.html",
        {
            "support": support,
        },
    )
    
from django.db.models import Q
from django.utils import timezone

from .models import (
    CarePlan,
    Assessment,
    CognitiveBehaviouralSupport,
    CareTask,
)

from .forms import (
    CarePlanForm,
    AssessmentForm,
    CognitiveBehaviouralSupportForm,
    CareTaskForm,
)

@login_required
@permission_required(
    "care.view_caretask",
    raise_exception=True,
)
def task_list(request):

    tasks = (
        CareTask.objects
        .select_related(
            "resident",
            "assigned_to",
            "assigned_to__user",
        )
        .all()
    )

    query = request.GET.get("q", "").strip()

    if query:

        tasks = tasks.filter(
            Q(title__icontains=query)
            |
            Q(resident__first_name__icontains=query)
            |
            Q(resident__last_name__icontains=query)
        )

    status = request.GET.get("status")

    if status:
        tasks = tasks.filter(status=status)

    priority = request.GET.get("priority")

    if priority:
        tasks = tasks.filter(priority=priority)

    return render(
        request,
        "care/task_list.html",
        {
            "tasks": tasks,
            "query": query,
            "status": status,
            "priority": priority,
            "status_choices": CareTask.STATUS_CHOICES,
            "priority_choices": CareTask.PRIORITY_CHOICES,
        },
    )
    
@login_required
@permission_required(
    "care.add_caretask",
    raise_exception=True,
)
def task_create(request):

    resident_id = request.GET.get("resident")

    initial = {}

    if resident_id:
        initial["resident"] = resident_id

    if request.method == "POST":

        form = CareTaskForm(request.POST)

        if form.is_valid():

            task = form.save()

            messages.success(
                request,
                "Care task created successfully.",
            )

            return redirect(
                "task_detail",
                pk=task.pk,
            )

    else:

        form = CareTaskForm(
            initial=initial
        )

    return render(
        request,
        "care/task_form.html",
        {
            "form": form,
            "title": "Create Care Task",
            "button_text": "Create Task",
        },
    )
    
@login_required
@permission_required(
    "care.view_caretask",
    raise_exception=True,
)
def task_detail(request, pk):

    task = get_object_or_404(
        CareTask.objects.select_related(
            "resident",
            "assigned_to",
            "assigned_to__user",
            "completed_by",
            "completed_by__user",
        ),
        pk=pk,
    )

    return render(
        request,
        "care/task_detail.html",
        {
            "task": task,
        },
    )
    
@login_required
@permission_required(
    "care.change_caretask",
    raise_exception=True,
)
def task_edit(request, pk):

    task = get_object_or_404(
        CareTask,
        pk=pk,
    )

    if request.method == "POST":

        form = CareTaskForm(
            request.POST,
            instance=task,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Care task updated successfully.",
            )

            return redirect(
                "task_detail",
                pk=task.pk,
            )

    else:

        form = CareTaskForm(
            instance=task,
        )

    return render(
        request,
        "care/task_form.html",
        {
            "form": form,
            "task": task,
            "title": "Edit Care Task",
            "button_text": "Save Changes",
        },
    )
    
@login_required
@permission_required(
    "care.change_caretask",
    raise_exception=True,
)
def task_complete(request, pk):

    task = get_object_or_404(
        CareTask,
        pk=pk,
    )

    if request.method == "POST":

        task.status = "completed"
        task.completed_at = timezone.now()

        staff_member = getattr(
            request.user,
            "staff_member",
            None,
        )

        if staff_member:
            task.completed_by = staff_member

        task.save(
            update_fields=[
                "status",
                "completed_at",
                "completed_by",
                "updated_at",
            ]
        )

        messages.success(
            request,
            "Care task marked as completed.",
        )

    return redirect(
        "task_detail",
        pk=task.pk,
    )
    
@login_required
@permission_required(
    "care.delete_caretask",
    raise_exception=True,
)
def task_delete(request, pk):

    task = get_object_or_404(
        CareTask,
        pk=pk,
    )

    if request.method == "POST":

        task.delete()

        messages.success(
            request,
            "Care task deleted.",
        )

        return redirect(
            "task_list"
        )

    return render(
        request,
        "care/task_delete.html",
        {
            "task": task,
        },
    )

from django.contrib import messages
from django.contrib.auth.decorators import (
    login_required,
    permission_required,
)
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone

from staff.models import StaffMember

from .forms import CareTaskForm
from .models import CareTask

@login_required
@permission_required(
    "care.view_caretask",
    raise_exception=True,
)
def task_list(request):

    tasks = (
        CareTask.objects
        .select_related(
            "resident",
            "assigned_to",
            "completed_by",
        )
        .order_by(
            "due_date",
            "due_time",
        )
    )

    status = request.GET.get("status")
    priority = request.GET.get("priority")
    task_type = request.GET.get("task_type")

    if status:
        tasks = tasks.filter(status=status)

    if priority:
        tasks = tasks.filter(priority=priority)

    if task_type:
        tasks = tasks.filter(task_type=task_type)

    return render(
        request,
        "tasks/task_list.html",
        {
            "tasks": tasks,
            "status": status,
            "priority": priority,
            "task_type": task_type,
            "status_choices": CareTask.STATUS_CHOICES,
            "priority_choices": CareTask.PRIORITY_CHOICES,
            "task_type_choices": CareTask.TASK_TYPE_CHOICES,
        },
    )
    
@login_required
@permission_required(
    "care.view_caretask",
    raise_exception=True,
)
def task_detail(request, pk):

    task = get_object_or_404(
        CareTask.objects.select_related(
            "resident",
            "assigned_to",
            "completed_by",
        ),
        pk=pk,
    )

    return render(
        request,
        "tasks/task_detail.html",
        {
            "task": task,
        },
    )
    
@login_required
@permission_required(
    "care.add_caretask",
    raise_exception=True,
)
def task_create(request):

    resident_id = request.GET.get("resident")

    initial = {}

    if resident_id:
        initial["resident"] = resident_id

    if request.method == "POST":

        form = CareTaskForm(request.POST)

        if form.is_valid():

            task = form.save()

            messages.success(
                request,
                "Care task created successfully.",
            )

            return redirect(
                "task_detail",
                pk=task.pk,
            )

    else:

        form = CareTaskForm(
            initial=initial
        )

    return render(
        request,
        "tasks/task_form.html",
        {
            "form": form,
            "title": "Create Care Task",
            "button_text": "Create Task",
        },
    )
    
@login_required
@permission_required(
    "care.change_caretask",
    raise_exception=True,
)
def task_edit(request, pk):

    task = get_object_or_404(
        CareTask,
        pk=pk,
    )

    if request.method == "POST":

        form = CareTaskForm(
            request.POST,
            instance=task,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Care task updated successfully.",
            )

            return redirect(
                "task_detail",
                pk=task.pk,
            )

    else:

        form = CareTaskForm(
            instance=task
        )

    return render(
        request,
        "tasks/task_form.html",
        {
            "form": form,
            "task": task,
            "title": "Edit Care Task",
            "button_text": "Save Changes",
        },
    )
@login_required
@permission_required(
    "care.change_caretask",
    raise_exception=True,
)
def task_complete(request, pk):

    task = get_object_or_404(
        CareTask,
        pk=pk,
    )

    staff = get_object_or_404(
        StaffMember,
        user=request.user,
    )

    if request.method == "POST":

        task.status = "completed"

        task.completed_at = timezone.now()

        task.completed_by = staff

        notes = request.POST.get(
            "notes",
            "",
        ).strip()

        if notes:
            task.notes = notes

        task.save()

        messages.success(
            request,
            "Care task marked as completed.",
        )

        return redirect(
            "task_detail",
            pk=task.pk,
        )

    return render(
        request,
        "tasks/task_complete.html",
        {
            "task": task,
        },
    )
    
@login_required
@permission_required(
    "care.change_caretask",
    raise_exception=True,
)
def task_start(request, pk):

    task = get_object_or_404(
        CareTask,
        pk=pk,
    )

    if request.method == "POST":

        task.status = "in_progress"
        task.save()

        messages.success(
            request,
            "Care task started.",
        )

    return redirect(
        "task_detail",
        pk=task.pk,
    )
    
@login_required
@permission_required(
    "care.change_caretask",
    raise_exception=True,
)
def task_cancel(request, pk):

    task = get_object_or_404(
        CareTask,
        pk=pk,
    )

    if request.method == "POST":

        task.status = "cancelled"
        task.save()

        messages.success(
            request,
            "Care task cancelled.",
        )

    return redirect(
        "task_detail",
        pk=task.pk,
    )
    
@login_required
@permission_required(
    "care.delete_caretask",
    raise_exception=True,
)
def task_delete(request, pk):

    task = get_object_or_404(
        CareTask,
        pk=pk,
    )

    if request.method == "POST":

        task.delete()

        messages.success(
            request,
            "Care task deleted.",
        )

        return redirect(
            "task_list"
        )

    return render(
        request,
        "tasks/task_delete.html",
        {
            "task": task,
        },
    )