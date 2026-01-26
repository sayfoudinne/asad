from django.db import models


class SchoolClass(models.Model):
    name = models.CharField(max_length=50, unique=True)  # bijv. "MBO4A"

    def __str__(self):
        return self.name


class Student(models.Model):
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.PROTECT, related_name="students")

    class Meta:
        ordering = ["first_name", "last_name"]  # Osiris volgorde

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.school_class})"


class ViolationType(models.Model):
    """
    Docent kan zelf soorten overtredingen bepalen + zwaarte (1-5)
    """
    name = models.CharField(max_length=120, unique=True)   # "Te laat", "Telefoon"
    severity = models.PositiveSmallIntegerField(default=1) # 1-5
    allow_free_text_amount = models.BooleanField(
        default=False,
        help_text="Bijv. te laat komen: docent kan minuten invullen."
    )

    def __str__(self):
        return f"{self.name} (zwaarte {self.severity})"


class Sanction(models.Model):
    """
    Mogelijke sancties (bord vegen, strafwerk, etc.)
    """
    name = models.CharField(max_length=120, unique=True)
    min_severity = models.PositiveSmallIntegerField(default=1)
    max_severity = models.PositiveSmallIntegerField(default=5)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Violation(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="violations")
    violation_type = models.ForeignKey(ViolationType, on_delete=models.PROTECT, related_name="violations")

    created_at = models.DateTimeField(auto_now_add=True)

    amount_text = models.CharField(max_length=50, blank=True)
    
    severity = models.PositiveSmallIntegerField(
        null=True, 
        blank=True,
        help_text="Zwaarte van deze overtreding (1-5). Laat leeg om de standaard zwaarte van het type te gebruiken."
    )

    proposed_sanction = models.ForeignKey(
        Sanction, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="proposed_for"
    )

    final_sanction_text = models.CharField(max_length=200, blank=True)

    def get_severity(self):
        """Retourneer de severity van deze violation, of de severity van het type als niet ingesteld"""
        return self.severity if self.severity is not None else self.violation_type.severity

    def __str__(self):
        return f"{self.student} - {self.violation_type} @ {self.created_at:%Y-%m-%d %H:%M}"
