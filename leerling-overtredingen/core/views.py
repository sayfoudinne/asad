from django.shortcuts import render
from .models import SchoolClass, Student

def home(request):
    return render(request, "core/home.html")

def students_list(request):
    classes = SchoolClass.objects.all()
    selected = request.GET.get("klas")

    students = Student.objects.all()
    if selected:
        students = students.filter(school_class__name=selected)

    context = {
        "classes": classes,
        "students": students,
        "selected": selected,
    }
    return render(request, "core/students_list.html", context)
import random
from django.shortcuts import render, redirect, get_object_or_404
from .models import SchoolClass, Student, ViolationType, Sanction, Violation
from .forms import ViolationForm


def students_list(request):
    classes = SchoolClass.objects.all()
    selected = request.GET.get("klas")

    students = Student.objects.all()
    if selected:
        students = students.filter(school_class__name=selected)

    return render(request, "core/students_list.html", {
        "classes": classes,
        "students": students,
        "selected": selected,
    })


def student_detail(request, student_id: int):
    student = get_object_or_404(Student, id=student_id)
    violations = student.violations.select_related("violation_type", "proposed_sanction").order_by("-created_at")
    return render(request, "core/student_detail.html", {
        "student": student,
        "violations": violations,
    })

def violation_create(request, student_id=None):
    initial = {}
    if student_id is not None:
        initial["student"] = get_object_or_404(Student, id=student_id)

    if request.method == "POST":
        form = ViolationForm(request.POST, initial=initial)
        if form.is_valid():
            violation: Violation = form.save(commit=False)

            sev = violation.violation_type.severity
            possible = Sanction.objects.filter(active=True, min_severity__lte=sev, max_severity__gte=sev)
            proposed = random.choice(list(possible)) if possible.exists() else None

            violation.proposed_sanction = proposed

            if not violation.final_sanction_text and proposed:
                violation.final_sanction_text = proposed.name

            violation.save()
            return redirect("student_detail", student_id=violation.student.id)
    else:
        form = ViolationForm(initial=initial)

    return render(request, "core/violation_form.html", {"form": form})

from django.contrib import messages
from .forms import ViolationForm, ViolationEditForm  # voeg ViolationEditForm toe

def violation_edit(request, violation_id: int):
    violation = get_object_or_404(Violation, id=violation_id)

    if request.method == "POST":
        form = ViolationEditForm(request.POST, instance=violation)
        if form.is_valid():
            updated = form.save(commit=False)

            # als overtreding-type verandert, update voorgestelde sanctie opnieuw
            sev = updated.violation_type.severity
            possible = Sanction.objects.filter(active=True, min_severity__lte=sev, max_severity__gte=sev)
            updated.proposed_sanction = random.choice(list(possible)) if possible.exists() else None

            # als docent final leeg laat, vul met voorgestelde
            if not updated.final_sanction_text and updated.proposed_sanction:
                updated.final_sanction_text = updated.proposed_sanction.name

            updated.save()
            messages.success(request, "Overtreding aangepast ✅")
            return redirect("student_detail", student_id=updated.student.id)
    else:
        form = ViolationEditForm(instance=violation)

    return render(request, "core/violation_edit.html", {"form": form, "violation": violation})


def violation_delete(request, violation_id: int):
    violation = get_object_or_404(Violation, id=violation_id)
    student_id = violation.student.id

    if request.method == "POST":
        violation.delete()
        messages.success(request, "Overtreding verwijderd ✅")
        return redirect("student_detail", student_id=student_id)

    return render(request, "core/violation_delete_confirm.html", {"violation": violation})
