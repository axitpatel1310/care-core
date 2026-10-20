from django.contrib import messages
from django.contrib.auth.decorators import (
    login_required,
    permission_required,
)
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.scoping import (
    get_visible_object_or_404,
    limit_resident_choices,
    scope_for_model,
)
from carecore.pagination import paginate
from residents.models import Resident

from .forms import (
    AssessmentForm,
    CarePlanForm,
    CareTaskForm,
    CognitiveBehaviouralSupportForm,
)
from .models import (
    Assessment,
    CarePlan,
    CareTask,
    CognitiveBehaviouralSupport,
)


@login_required
@permission_required(
    "care.view_careplan",
    raise_exception=True,
)
def care_plan_list(request):

    care_plans = scope_for_model(
        CarePlan.objects.select_related(
            "resident",
            "responsible_staff",
            "created_by",
        ).all(),
        request.user,
    )

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

    page, filter_query = paginate(request, care_plans)

    return render(
        request,
        "care/care_plan_list.html",
        {
            "care_plans": page,
            "page": page,
            "filter_query": filter_query,
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
        resident = get_visible_object_or_404(
            request.user,
            Resident,
            pk=resident_id,
        )

        initial["resident"] = resident

    if request.method == "POST":

        form = CarePlanForm(request.POST)
        limit_resident_choices(form, request.user)

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
        limit_resident_choices(form, request.user)

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

    care_plan = get_visible_object_or_404(
        request.user,
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

    care_plan = get_visible_object_or_404(
        request.user,
        CarePlan,
        pk=pk,
    )

    if request.method == "POST":

        form = CarePlanForm(
            request.POST,
            instance=care_plan,
        )
        limit_resident_choices(form, request.user)

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
        limit_resident_choices(form, request.user)

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

    care_plan = get_visible_object_or_404(
        request.user,
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

    assessments = scope_for_model(
        Assessment.objects.select_related(
            "resident",
            "performed_by",
        ).all(),
        request.user,
    )

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

    page, filter_query = paginate(request, assessments)

    return render(
        request,
        "care/assessment_list.html",
        {
            "assessments": page,
            "page": page,
            "filter_query": filter_query,
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

        resident = get_visible_object_or_404(
            request.user,
            Resident,
            pk=resident_id,
        )

        initial["resident"] = resident

    if request.method == "POST":

        form = AssessmentForm(request.POST)
        limit_resident_choices(form, request.user)

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
        limit_resident_choices(form, request.user)

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

    assessment = get_visible_object_or_404(
        request.user,
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

    assessment = get_visible_object_or_404(
        request.user,
        Assessment,
        pk=pk,
    )

    if request.method == "POST":

        form = AssessmentForm(
            request.POST,
            instance=assessment,
        )
        limit_resident_choices(form, request.user)

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
        limit_resident_choices(form, request.user)

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

    assessment = get_visible_object_or_404(
        request.user,
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
    

@login_required
@permission_required(
    "care.view_cognitivebehaviouralsupport",
    raise_exception=True,
)
def behavioural_support_list(request):

    supports = scope_for_model(
        CognitiveBehaviouralSupport.objects.select_related(
            "resident",
        ).all(),
        request.user,
    )

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

    page, filter_query = paginate(request, supports)

    return render(
        request,
        "care/behavioural_support_list.html",
        {
            "supports": page,
            "page": page,
            "filter_query": filter_query,
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

        resident = get_visible_object_or_404(
            request.user,
            Resident,
            pk=resident_id,
        )

        initial["resident"] = resident

    if request.method == "POST":

        form = CognitiveBehaviouralSupportForm(
            request.POST
        )
        limit_resident_choices(form, request.user)

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
        limit_resident_choices(form, request.user)

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

    support = get_visible_object_or_404(
        request.user,
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

    support = get_visible_object_or_404(
        request.user,
        CognitiveBehaviouralSupport,
        pk=pk,
    )

    if request.method == "POST":

        form = CognitiveBehaviouralSupportForm(
            request.POST,
            instance=support,
        )
        limit_resident_choices(form, request.user)

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
        limit_resident_choices(form, request.user)

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

    support = get_visible_object_or_404(
        request.user,
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
    


@login_required
@permission_required(
    "care.view_caretask",
    raise_exception=True,
)
def task_list(request):

    tasks = scope_for_model(
        (
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
        ),
        request.user,
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

    page, filter_query = paginate(request, tasks)

    return render(
        request,
        "tasks/task_list.html",
        {
            "tasks": page,
            "page": page,
            "filter_query": filter_query,
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

    task = get_visible_object_or_404(
        request.user,
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
        limit_resident_choices(form, request.user)

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
        limit_resident_choices(form, request.user)

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

    task = get_visible_object_or_404(
        request.user,
        CareTask,
        pk=pk,
    )

    if request.method == "POST":

        form = CareTaskForm(
            request.POST,
            instance=task,
        )
        limit_resident_choices(form, request.user)

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
        limit_resident_choices(form, request.user)

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

    task = get_visible_object_or_404(
        request.user,
        CareTask,
        pk=pk,
    )

    staff = getattr(
        request.user,
        "staff_profile",
        None,
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

    task = get_visible_object_or_404(
        request.user,
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

    task = get_visible_object_or_404(
        request.user,
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

    task = get_visible_object_or_404(
        request.user,
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
