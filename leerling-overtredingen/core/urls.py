from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("leerlingen/", views.students_list, name="students_list"),
    path("leerling/<int:student_id>/", views.student_detail, name="student_detail"),
    path("overtreding/nieuw/", views.violation_create, name="violation_create"),
    path("overtreding/nieuw/<int:student_id>/", views.violation_create, name="violation_create_for_student"),
    path("overtreding/<int:violation_id>/wijzig/", views.violation_edit, name="violation_edit"),
    path("overtreding/<int:violation_id>/verwijder/", views.violation_delete, name="violation_delete"),
    

]
