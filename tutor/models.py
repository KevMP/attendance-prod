from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta, datetime

class Semester(models.Model):
    start_week = models.DateField()
    end_week = models.DateField()

    def number_of_weeks(self):
        delta = self.end_week - self.start_week
        return (delta.days // 7) + 1  # +1 because we count the start week as a full week

    @staticmethod
    def get_semester():
        return Semester.objects.get(pk=1)
    
    @staticmethod
    def date_to_week_number(date):
        semester = Semester.get_semester()
        
        if not isinstance(date, datetime):
            date = datetime.combine(date, datetime.min.time())
        semester_start_date = datetime.combine(semester.start_week, datetime.min.time())
        delta = date - semester_start_date
        week_number = (delta.days // 7) + 1
        return week_number
    
    @staticmethod
    def week_number_to_date(week_number):
        """
        Given a week number within the semester, return the start and end dates of that week.
        """
        # Fetch the semester to use for calculation. Adjust this as necessary.
        semester = Semester.get_semester()
        
        # Ensure the semester's start_week is a datetime for calculation
        semester_start_date = datetime.combine(semester.start_week, datetime.min.time())

        # Calculate the date of the Monday of the given week number
        # Subtract 1 from week_number since week 1 starts on semester_start_date
        monday_date = semester_start_date + timedelta(days=(week_number - 1) * 7)

        # The semester_start_date is assumed to be a Monday. If not, adjust monday_date accordingly.
        return monday_date.date()

class Student(models.Model):
    email = models.EmailField(primary_key=True)
    id_number = models.CharField(max_length=10)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)

    def __str__(self):
        return self.first_name + " " + self.last_name
    
    def get_enrolled_classes(self):
        classes = ClassEnrollment.objects.filter(student=self)
        return [c.enrolled_class for c in classes]
    
    def get_attendance_for_week(self, week_number, class_pk):
        class_obj = Class.objects.get(pk=class_pk)

        attendance_record = AttendanceRecord.objects.filter(student=self, class_ref=class_obj, week=int(week_number)).first()

        if(attendance_record):
            return attendance_record.attended
        else:
            return False


class Class(models.Model):
    class_code = models.CharField(max_length=10)
    class_name = models.CharField(max_length=100)
    professor = models.CharField(max_length=100)

    def __str__(self):
        return self.class_name + " " + self.professor
    
    def get_pk(self):
        return self.pk
        

class ClassEnrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    enrolled_class = models.ForeignKey(Class, on_delete=models.CASCADE)
    enrollment_date = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = [['student', 'enrolled_class']]

    def __str__(self):
        return f'{self.student} enrolled in {self.enrolled_class}'
    
class AttendanceRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    class_ref = models.ForeignKey(Class, on_delete=models.CASCADE)
    week = models.IntegerField(default = 1)
    attendance_type = models.CharField(max_length=100, help_text="Type of attendance")
    attended = models.BooleanField(default=False)
    recorded_by = models.ForeignKey(User, on_delete=models.CASCADE, help_text="User who recorded the attendance", null=True)

    class Meta:
        unique_together = [['student', 'class_ref', 'week']]

    def __str__(self):
        attendance_status = "attended" if self.attended else "missed"
        return f"{self.student} {attendance_status} {self.attendance_type} for {self.class_ref.class_name}"
    