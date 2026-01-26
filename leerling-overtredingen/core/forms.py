from django import forms
from .models import Violation, SchoolClass, Student, ViolationType
import csv


class ViolationForm(forms.ModelForm):
    severity = forms.ChoiceField(
        label="Zwaarte",
        choices=[('', '-- Gebruik standaard zwaarte van type --')] + [(str(i), f'Zwaarte {i}') for i in range(1, 6)],
        required=False,
        help_text="Optioneel: overschrijf de standaard zwaarte van het overtredingstype",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = Violation
        fields = ["student", "violation_type", "severity", "amount_text", "final_sanction_text"]
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
    
    def clean_severity(self):
        severity = self.cleaned_data.get('severity')
        if severity:
            return int(severity)
        return None

    def __init__(self, *args, **kwargs):
        # optioneel: meegegeven klas om de leerlingen op te filteren
        school_class = kwargs.pop("school_class", None)
        super().__init__(*args, **kwargs)

        qs = Student.objects.all()
        if school_class:
            qs = qs.filter(school_class=school_class)
        self.fields["student"].queryset = qs


class ViolationEditForm(forms.ModelForm):
    severity = forms.ChoiceField(
        label="Zwaarte",
        choices=[('', '-- Gebruik standaard zwaarte van type --')] + [(str(i), f'Zwaarte {i}') for i in range(1, 6)],
        required=False,
        help_text="Optioneel: overschrijf de standaard zwaarte van het overtredingstype",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = Violation
        fields = ["violation_type", "severity", "amount_text", "final_sanction_text"]
        labels = {
            "violation_type": "Overtreding",
            "amount_text": "Opmerkingen",
            "final_sanction_text": "Definitief"
        }
        widgets = {
            "final_sanction_text": forms.TextInput(attrs={"placeholder": "Docent kan sanctie aanpassen..."})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Zet de huidige severity waarde als die bestaat
        if self.instance and self.instance.severity:
            self.fields['severity'].initial = str(self.instance.severity)
    
    def clean_severity(self):
        severity = self.cleaned_data.get('severity')
        if severity:
            return int(severity)
        return None


class CSVImportForm(forms.Form):
    csv_file = forms.FileField(
        label="CSV Bestand",
        help_text="Upload een CSV bestand met formaat: voornaam, achternaam, klas"
    )

    def process_csv(self):
        """Verwerk het CSV bestand en maak studenten aan"""
        csv_file = self.cleaned_data['csv_file']
        
        # Decodeer het bestand als tekst
        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.reader(decoded_file)
        
        created_students = []
        errors = []
        
        for row_num, row in enumerate(reader, start=1):
            if len(row) < 3:
                errors.append(f"Regel {row_num}: Onvoldoende kolommen (verwacht: voornaam, achternaam, klas)")
                continue
            
            voornaam = row[0].strip()
            achternaam = row[1].strip()
            klas_naam = row[2].strip()
            
            if not voornaam or not achternaam or not klas_naam:
                errors.append(f"Regel {row_num}: Lege waarden gevonden")
                continue
            
            # Haal of maak de klas aan
            school_class, created = SchoolClass.objects.get_or_create(name=klas_naam)
            
            # Maak de student aan (voorkom duplicaten)
            student, created = Student.objects.get_or_create(
                first_name=voornaam,
                last_name=achternaam,
                school_class=school_class
            )
            
            if created:
                created_students.append(student)
        
        return created_students, errors


class ViolationFilterForm(forms.Form):
    """Formulier voor het filteren van overtredingen"""
    date_from = forms.DateField(
        label="Van datum",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        label="Tot datum",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    violation_type = forms.ModelChoiceField(
        label="Type overtreding",
        queryset=ViolationType.objects.all().order_by('name'),
        required=False,
        empty_label="-- Alle types --",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    severity = forms.ChoiceField(
        label="Zwaarte",
        choices=[('', '-- Alle zwaartes --')] + [(str(i), f'Zwaarte {i}') for i in range(1, 6)],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
