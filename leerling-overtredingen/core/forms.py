from django import forms
from .models import Violation

class ViolationForm(forms.ModelForm):
    class Meta:
        model = Violation
        fields = ["student", "violation_type", "amount_text", "final_sanction_text"]
        widgets = {
            "final_sanction_text": forms.TextInput(attrs={"placeholder": "Docent kan sanctie aanpassen..."})
        }

from django import forms
from .models import Violation

class ViolationEditForm(forms.ModelForm):
    class Meta:
        model = Violation
        fields = ["violation_type", "amount_text", "final_sanction_text"]
