from django import forms
from .models import CarePlan, Assessment, CognitiveBehaviouralSupport
from .models import CarePlan,Assessment
from .models import CarePlan, Assessment, CognitiveBehaviouralSupport, CareTask

class CarePlanForm(forms.ModelForm):

    class Meta:
        model = CarePlan

        fields = [
            "resident",
            "responsible_staff",
            "last_reviewed",
            "next_review",
            "mobility",
            "nutrition",
            "personal_care",
            "communication",
            "cognitive_support",
            "behavioural_support",
            "status",
            "notes",
        ]

        widgets = {
            "last_reviewed": forms.DateInput(
                attrs={"type": "date"}
            ),

            "next_review": forms.DateInput(
                attrs={"type": "date"}
            ),

            "mobility": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Mobility requirements and care instructions...",
                }
            ),

            "nutrition": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Nutrition and dietary requirements...",
                }
            ),

            "personal_care": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Personal care requirements...",
                }
            ),

            "communication": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Communication requirements and preferences...",
                }
            ),

            "cognitive_support": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Cognitive support requirements...",
                }
            ),

            "behavioural_support": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Behavioural support requirements...",
                }
            ),

            "notes": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Additional care plan notes...",
                }
            ),
        }

class AssessmentForm(forms.ModelForm):

    class Meta:
        model = Assessment

        fields = [
            "resident",
            "assessment_type",
            "assessment_date",
            "performed_by",
            "result",
            "notes",
            "next_review",
        ]

        widgets = {
            "assessment_date": forms.DateInput(
                attrs={"type": "date"}
            ),

            "next_review": forms.DateInput(
                attrs={"type": "date"}
            ),

            "result": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Assessment findings and results...",
                }
            ),

            "notes": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Additional notes...",
                }
            ),
        }
        
class CognitiveBehaviouralSupportForm(forms.ModelForm):

    class Meta:
        model = CognitiveBehaviouralSupport

        fields = [
            "resident",
            "support_requirements",
            "known_triggers",
            "communication_preferences",
            "behaviour_observations",
            "de_escalation_strategies",
            "care_instructions",
        ]

        widgets = {
            "support_requirements": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Describe the resident's support requirements...",
                }
            ),

            "known_triggers": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Known triggers or situations to avoid...",
                }
            ),

            "communication_preferences": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Preferred communication methods...",
                }
            ),

            "behaviour_observations": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Relevant behavioural observations...",
                }
            ),

            "de_escalation_strategies": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Recommended de-escalation strategies...",
                }
            ),

            "care_instructions": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "Specific care instructions...",
                }
            ),
        }
        
class CareTaskForm(forms.ModelForm):

    class Meta:
        model = CareTask

        fields = [
            "resident",
            "assigned_to",
            "title",
            "description",
            "task_type",
            "priority",
            "due_date",
            "due_time",
            "status",
            "notes",
        ]

        widgets = {
            "due_date": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),

            "due_time": forms.TimeInput(
                attrs={
                    "type": "time",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Describe what needs to be done...",
                }
            ),

            "notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Additional notes...",
                }
            ),
        }
        
from django import forms

from .models import CareTask
