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
    classes = SchoolClass.objects.all()
    initial = {}
    school_class = None

    # klas gekozen via filter (GET) of behouden via hidden field (POST)
    selected = request.GET.get("klas") or request.POST.get("klas")

    # als we via een specifieke leerling komen, zet die alvast vast
    if student_id is not None:
        student = get_object_or_404(Student, id=student_id)
        initial["student"] = student
        selected = student.school_class.name

    if selected:
        school_class = SchoolClass.objects.filter(name=selected).first()

    if request.method == "POST":
        form = ViolationForm(request.POST, initial=initial, school_class=school_class)
        if form.is_valid():
            violation: Violation = form.save(commit=False)

            sev = violation.violation_type.severity
            possible = Sanction.objects.filter(
                active=True,
                min_severity__lte=sev,
                max_severity__gte=sev,
            )
            proposed = random.choice(list(possible)) if possible.exists() else None

            violation.proposed_sanction = proposed

            if not violation.final_sanction_text and proposed:
                violation.final_sanction_text = proposed.name

            violation.save()
            return redirect("student_detail", student_id=violation.student.id)
    else:
        form = ViolationForm(initial=initial, school_class=school_class)

    return render(
        request,
        "core/violation_form.html",
        {"form": form, "classes": classes, "selected": selected},
    )

from django.contrib import messages
from .forms import ViolationForm, ViolationEditForm  # voeg ViolationEditForm toe

def violation_edit(request, violation_id: int):
    violation = get_object_or_404(Violation, id=violation_id)

    if request.method == "POST":
        form = ViolationEditForm(request.POST, instance=violation)
        if form.is_valid():
            updated = form.save(commit=False)

            # Gebruik de severity van de violation, of de severity van het type als niet ingesteld
            sev = updated.get_severity()
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


from django.db.models import Count, Q
from django.utils import timezone
from .forms import ViolationFilterForm


def class_overview(request):
    """Overzicht van alle klassen met statistieken"""
    classes = SchoolClass.objects.annotate(
        total_students=Count('students'),
        total_violations=Count('students__violations'),
        students_with_violations=Count('students', filter=Q(students__violations__isnull=False), distinct=True)
    ).order_by('name')
    
    # Voeg extra statistieken toe per klas
    classes_with_stats = []
    for school_class in classes:
        violations = Violation.objects.filter(student__school_class=school_class)
        
        # Overtredingen per type
        violations_by_type = violations.values('violation_type__name').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Meest voorkomende overtredingen
        top_violations = violations_by_type[:5]
        
        # Studenten met meeste overtredingen
        top_students = Student.objects.filter(
            school_class=school_class
        ).annotate(
            violation_count=Count('violations')
        ).filter(
            violation_count__gt=0
        ).order_by('-violation_count')[:5]
        
        classes_with_stats.append({
            'class': school_class,
            'total_students': school_class.total_students,
            'total_violations': school_class.total_violations,
            'students_with_violations': school_class.students_with_violations,
            'violations_by_type': top_violations,
            'top_students': top_students,
        })
    
    return render(request, "core/class_overview.html", {
        "classes_with_stats": classes_with_stats,
    })


def class_detail(request, class_id: int):
    """Gedetailleerd overzicht van een specifieke klas"""
    school_class = get_object_or_404(SchoolClass, id=class_id)
    
    # Initialiseer filterformulier
    filter_form = ViolationFilterForm(request.GET)
    
    # Basis queryset voor alle overtredingen in deze klas
    violations = Violation.objects.filter(
        student__school_class=school_class
    ).select_related('student', 'violation_type', 'proposed_sanction')
    
    # Bouw filter voor violations (gebruikt ook voor student violations)
    violation_filter = Q()
    has_active_filters = False
    
    if filter_form.is_valid():
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        violation_type = filter_form.cleaned_data.get('violation_type')
        severity = filter_form.cleaned_data.get('severity')
        
        if date_from:
            violation_filter &= Q(created_at__date__gte=date_from)
            has_active_filters = True
        if date_to:
            violation_filter &= Q(created_at__date__lte=date_to)
            has_active_filters = True
        if violation_type:
            violation_filter &= Q(violation_type=violation_type)
            has_active_filters = True
        if severity:
            violation_filter &= Q(violation_type__severity=int(severity))
            has_active_filters = True
    
    # Pas filters toe op violations
    if violation_filter:
        violations = violations.filter(violation_filter)
    
    # Sorteer op datum (nieuwste eerst)
    violations = violations.order_by('-created_at')
    
    # Alle studenten in deze klas (met violation count gebaseerd op gefilterde violations)
    # Gebruik violation IDs in plaats van Q filter om problemen te voorkomen
    if violation_filter:
        # Haal de IDs van gefilterde violations op
        filtered_violation_ids = list(violations.values_list('id', flat=True))
        if filtered_violation_ids:
            students = Student.objects.filter(school_class=school_class).annotate(
                violation_count=Count('violations', filter=Q(id__in=filtered_violation_ids))
            ).order_by('-violation_count', 'first_name', 'last_name')
        else:
            # Geen violations voldoen aan de filters
            students = Student.objects.filter(school_class=school_class).annotate(
                violation_count=Count('violations', filter=Q(id__in=[]))
            ).order_by('first_name', 'last_name')
    else:
        # Geen filters actief, tel alle violations
        students = Student.objects.filter(school_class=school_class).annotate(
            violation_count=Count('violations')
        ).order_by('-violation_count', 'first_name', 'last_name')
    
    # Statistieken per overtredingstype (gefilterd)
    violations_by_type = violations.values(
        'violation_type__name',
        'violation_type__severity'
    ).annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Overtredingen per dag (laatste 30 dagen, gefilterd)
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.now() - timedelta(days=30)
    violations_by_date = violations.filter(
        created_at__gte=thirty_days_ago
    ).extra(
        select={'day': 'date(created_at)'}
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    # Totaal aantal overtredingen (gefilterd)
    total_violations = violations.count()
    
    # Aantal studenten met overtredingen (gefilterd)
    students_with_violations = students.filter(violation_count__gt=0).count()
    
    # Gemiddeld aantal overtredingen per student
    avg_violations = total_violations / students.count() if students.count() > 0 else 0
    
    # Meest voorkomende overtredingstype
    most_common_type = violations_by_type.first() if violations_by_type else None
    
    
    context = {
        'school_class': school_class,
        'students': students,
        'violations': violations[:50],  # Laatste 50 overtredingen
        'violations_by_type': violations_by_type,
        'violations_by_date': list(violations_by_date),
        'total_violations': total_violations,
        'students_with_violations': students_with_violations,
        'total_students': students.count(),
        'avg_violations': round(avg_violations, 2),
        'most_common_type': most_common_type,
        'filter_form': filter_form,
        'has_active_filters': has_active_filters,
    }
    
    return render(request, "core/class_detail.html", context)