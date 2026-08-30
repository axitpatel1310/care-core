from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import (
    ComplianceDocument,
    Risk,
    Audit,
    CorrectiveAction,
)


@login_required
def compliance_dashboard(request):
    context = {
        "documents": ComplianceDocument.objects.all(),
        "risks": Risk.objects.all(),
        "audits": Audit.objects.all(),
        "actions": CorrectiveAction.objects.all(),
    }

    return render(
        request,
        "compliance/dashboard.html",
        context,
    )