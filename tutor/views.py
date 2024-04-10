import os
import shutil
from datetime import datetime
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User, Group
from django.conf import settings
from app.decorators import role_required
from .forms import WorkshopUpload, ImportStudentData
from .models import Class, AttendanceRecord, Student, Semester, ClassEnrollment
from django.contrib import messages


@role_required('Tutor')
def home(request):
    if request.method == "POST":
        formobj = WorkshopUpload(request.POST, request.FILES)

        try:
            if formobj.is_valid():
                report = formobj.process_attendance(request.user)
                upload_form = WorkshopUpload()#upload report 
                classes = Class.objects.all()
                students = Student.objects.all()
                semester = Semester.get_semester()
                # Calculate the number of weeks for the current semester
                semester_weeks = range(1, semester.number_of_weeks() + 1)
                return render(request, "home.html", {
                    'upload_form': upload_form, 
                    'classes': classes, #object with methods
                    'students': students, #object with methods
                    'semester_weeks': semester_weeks,#number of weeks
                    'report' : report
                })
            
            else:
                messages.warning(request, 'There was a problem with your submission. Please check the form for errors.')
                return redirect(home)
        except Exception:
            messages.warning(request, 'FATAL ERROR, CONTACT KEVIN')
            return redirect(home)

    else:
        upload_form = WorkshopUpload()#upload report 
        classes = Class.objects.all()
        students = Student.objects.all()
        semester = Semester.get_semester()

        # Calculate the number of weeks for the current semester
        semester_weeks = range(1, semester.number_of_weeks() + 1)

        return render(request, "home.html", {
            'upload_form': upload_form, 
            'classes': classes, #object with methods
            'students': students, #object with methods
            'semester_weeks': semester_weeks#number of weeks
        })

@role_required('Lead', 'Manager')
def handle_semester_data(request):
    if request.method == "POST":
        import_form = ImportStudentData(request.POST, request.FILES)
        if import_form.is_valid():
            try:
                import_form.process()
            except:
                messages.warning(request, 'ERROR IMPORTING DATA.')
        
        clean_form = ImportStudentData()
        return render(request, 'handleSemester.html', {'form':clean_form})

    else:
        import_form = ImportStudentData()
        return render(request, 'handleSemester.html', {'form':import_form})

def landing_page(request):
    return render(request, "landingPage.html")

def update_attendance(request):
    if request.method == 'POST':
        # Directly access the POST data fields
        studentEmail = request.POST.get('studentEmail')
        classId = request.POST.get('classId')
        week = request.POST.get('week')
        checked = request.POST.get('checked')#checkbox, was acting funcky so just replaced the logic but well keep it just in case
        
        record_exists, created = AttendanceRecord.objects.get_or_create(
            student=Student.objects.get(pk=studentEmail),
            class_ref=Class.objects.get(pk=classId),
            week=int(week)
        )
        
        record_exists.attended = not record_exists.attended
        record_exists.recorded_by = request.user
        record_exists.attendance_type = "Manual"
        
        record_exists.save()
        return JsonResponse({"status": "success", "message": "Attendance updated successfully"})
    else:
        return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)


@require_POST  # Ensure this view can only be accessed via POST method
@role_required('Lead', 'Manager')
def clear_semester_data(request):
    if request.POST.get('confirmation_text') == 'CONFIRM CLEAR':
        try:
            # Your logic to clear the data goes here
            # For example, Semester.objects.all().delete()
            print("IM IN HERE YUH")
            db_path = settings.DATABASES['default']['NAME']
            backup_path = os.path.join(os.path.dirname(db_path), 'dbBackups/backup_{}.sqlite3'.format(datetime.now().strftime('%Y%m%d%H%M%S')))
            shutil.copyfile(db_path, backup_path)

            AttendanceRecord.objects.all().delete()
            ClassEnrollment.objects.all().delete()
            Student.objects.all().delete()

            group = Group.objects.get(name="Student")
            users_in_group = User.objects.filter(groups=group)
            users_in_group.delete()


            return JsonResponse({'success': True, 'message': 'All semester data has been cleared successfully.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'There was a problem clearing the semester data: %s' % str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request or incorrect confirmation text.'})