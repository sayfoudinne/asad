from django.contrib import admin
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import path
from django.utils.html import format_html
from django.urls import reverse
from .models import SchoolClass, Student, ViolationType, Sanction, Violation
from .forms import CSVImportForm


class CustomAdminSite(admin.AdminSite):
    site_header = 'DocentenSite Admin'
    site_title = 'DocentenSite Admin'
    index_title = 'Beheer'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-csv/', self.admin_view(self.import_csv_view), name='core_student_import_csv'),
        ]
        return custom_urls + urls
    
    def import_csv_view(self, request):
        """Custom view voor CSV import"""
        if request.method == 'POST':
            form = CSVImportForm(request.POST, request.FILES)
            if form.is_valid():
                created_students, errors = form.process_csv()
                
                if created_students:
                    messages.success(
                        request,
                        f'Succesvol {len(created_students)} student(en) geïmporteerd.'
                    )
                
                if errors:
                    for error in errors:
                        messages.warning(request, error)
                
                if not created_students and not errors:
                    messages.info(request, 'Geen nieuwe studenten aangemaakt.')
                
                return redirect('admin:core_student_import_csv')
        else:
            form = CSVImportForm()
        
        context = {
            **self.each_context(request),
            'title': 'Studenten importeren',
            'form': form,
            'opts': Student._meta,
            'has_view_permission': True,
        }
        
        return render(request, 'admin/import_csv.html', context)
    
    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['import_url'] = reverse('admin:core_student_import_csv')
        return super().index(request, extra_context)


# Maak een custom admin site instance
admin_site = CustomAdminSite(name='admin')


class SchoolClassAdmin(admin.ModelAdmin):
    pass


class StudentAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'school_class']
    list_filter = ['school_class']
    search_fields = ['first_name', 'last_name']
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['import_url'] = reverse('admin:core_student_import_csv')
        return super().changelist_view(request, extra_context)


class ViolationTypeAdmin(admin.ModelAdmin):
    pass


class SanctionAdmin(admin.ModelAdmin):
    pass


class ViolationAdmin(admin.ModelAdmin):
    pass


# Registreer alle modellen op de custom admin site
admin_site.register(SchoolClass, SchoolClassAdmin)
admin_site.register(Student, StudentAdmin)
admin_site.register(ViolationType, ViolationTypeAdmin)
admin_site.register(Sanction, SanctionAdmin)
admin_site.register(Violation, ViolationAdmin)
