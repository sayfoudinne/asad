from django import forms
from .models import Violation, SchoolClass, Student


class ViolationForm(forms.ModelForm):
    class Meta:
        model = Violation
        fields = ["student", "violation_type", "amount_text", "final_sanction_text"]
        labels = {
            "student": "Leerling",
            "violation_type": "Overtreding",
            "amount_text": "Opmerkingen",
            "final_sanction_text": "Definitief",
        }
        widgets = {
            "final_sanction_text": forms.TextInput(
                attrs={"placeholder": "Docent kan sanctie aanpassen..."}
            )
        }

    def __init__(self, *args, **kwargs):
        # optioneel: meegegeven klas om de leerlingen op te filteren
        school_class = kwargs.pop("school_class", None)
        super().__init__(*args, **kwargs)

        qs = Student.objects.all()
        if school_class:
            qs = qs.filter(school_class=school_class)
        self.fields["student"].queryset = qs


class ViolationEditForm(forms.ModelForm):
    class Meta:
        model = Violation
        fields = ["violation_type", "amount_text", "final_sanction_text"]
        labels = {
            "violation_type": "Overtreding",
            "amount_text": "Opmerkingen",
            "final_sanction_text": "Definitief"
        }
        widgets = {
            "final_sanction_text": forms.TextInput(attrs={"placeholder": "Docent kan sanctie aanpassen..."})
        }
