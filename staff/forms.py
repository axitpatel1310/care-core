from django import forms
from residents.models import Resident
from .models import StaffMember, ResidentStaffAssignment
from .models import StaffMember


class StaffMemberForm(forms.ModelForm):

    class Meta:
        model = StaffMember

        fields = [
            "user",
            "employee_id",
            "facility",
            "ward",
            "phone",
            "qualifications",
            "employment_status",
        ]

        widgets = {
            "employee_id": forms.TextInput(
                attrs={
                    "placeholder": "EMP-001",
                }
            ),

            "phone": forms.TextInput(
                attrs={
                    "placeholder": "+49 ...",
                }
            ),

            "qualifications": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Professional qualifications...",
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields["user"].label = "User Account"
        self.fields["employee_id"].label = "Employee ID"
        self.fields["facility"].label = "Facility"
        self.fields["ward"].label = "Ward"
        self.fields["phone"].label = "Phone"
        self.fields["qualifications"].label = "Qualifications"
        self.fields["employment_status"].label = "Employment Status"
        
class ResidentStaffAssignmentForm(forms.ModelForm):

    class Meta:
        model = ResidentStaffAssignment

        fields = [
            "staff",
            "resident",
            "role",
            "start_date",
            "end_date",
            "is_active",
            "notes",
        ]

        widgets = {
            "start_date": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),

            "end_date": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),

            "notes": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Assignment notes...",
                }
            ),
        }