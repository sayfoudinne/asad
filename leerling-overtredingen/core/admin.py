from django.contrib import admin
from .models import SchoolClass, Student, ViolationType, Sanction, Violation

admin.site.register(SchoolClass)
admin.site.register(Student)
admin.site.register(ViolationType)
admin.site.register(Sanction)
admin.site.register(Violation)
