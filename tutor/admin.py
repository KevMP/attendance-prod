from django.contrib import admin
from .models import Student, Class, ClassEnrollment, AttendanceRecord, Semester

# Register your models here.
admin.site.register(Student)
admin.site.register(Class)
admin.site.register(ClassEnrollment)
admin.site.register(AttendanceRecord)
admin.site.register(Semester)