from app.decorators import role_required
from django.shortcuts import render
from tutor.models import Student, Semester, AttendanceRecord


@role_required("Student")
def home(request):
    context = {}
    context["week_number"] = Semester.get_semester().number_of_weeks()
    context["enrolled_classes"] = {}
    present_count = 0
    stu_obj = Student.objects.get(pk=request.user.username)

    for enrolled_class in stu_obj.get_enrolled_classes():
        class_weeks_data = []
        for week in range(1, context["week_number"] + 1):
            attendance_record = AttendanceRecord.objects.filter(student=stu_obj, class_ref=enrolled_class, week=week).first()
            if attendance_record:
                class_weeks_data.append({
                    "week": week,
                    "attendance_type": attendance_record.attendance_type,
                    "attended": attendance_record.attended,
                    "recorded_by": attendance_record.recorded_by,  # Add the recorder's name
                })

                if attendance_record.attended:
                    present_count +=1
                    
            else:
                # No record found, mark as absent with default recorder
                class_weeks_data.append({
                    "week": week,
                    "attendance_type": "Absent",
                    "attended": False,
                    "recorded_by": "N/A",  # Default value when no record exists
                })
        attendance_percentage = (present_count / context["week_number"]) * 100
        context["enrolled_classes"][enrolled_class] = {
            "weeks_data": class_weeks_data,
            "attendance_percentage": attendance_percentage
        }
    
    return render(request, 'studentView.html', context)

