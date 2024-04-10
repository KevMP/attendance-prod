import csv
from io import StringIO, TextIOWrapper
from django import forms
from .models import ClassEnrollment, Student, Class, Semester, AttendanceRecord
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group
from datetime import datetime
import traceback


class_options = (
    ("1", "C++"),
    ("2", "Java"),
    ("3", "Python")
)

class WorkshopUpload(forms.Form):
    class_choice = forms.ChoiceField(choices=class_options)
    no_participation = forms.CharField(max_length=200, required=False)
    chat_text = forms.FileField()
    report_csv = forms.FileField()
    ignore_duration = forms.BooleanField(required=False)

    # Temporary storage for file content
    _report_csv_content = None

    def clean_report_csv(self):
        # Read the content of the uploaded CSV file once and store it in memory
        csv_file = self.cleaned_data.get('report_csv')
        if csv_file:
            csv_file.seek(0)  # Ensure we're at the start
            content = csv_file.read().decode('utf-8-sig')
            self._report_csv_content = StringIO(content)  # Use StringIO to emulate a file with the in-memory string
        return csv_file

    def get_user_to_email(self):
        user_to_email = {}
        chat_file_contents = self.cleaned_data['chat_text']
        last_user = None

        for line in chat_file_contents:
            line = line.decode('utf-8').strip()
            line_parts = line.split()
            if "From" in line and "to Everyone:" in line:
                words = line.split(" ")
                split_start = words.index("From") +1
                split_end = words.index("to")
                last_user = " ".join(words[split_start:split_end]).strip()
            elif "@mymdc.net" in line and last_user != None:
                user_email = ""
                for part in line_parts:
                    if "@mymdc.net" in part:
                        user_email = part
                user_to_email[last_user.lower()] = user_email.lower()

        return user_to_email

    def get_user_to_time(self):
        user_to_time = {}
        self._report_csv_content.seek(0)  # Ensure pointer is at the start for re-reading
        reader = csv.reader(self._report_csv_content)

        row_count = 0
        for row in reader:
            row_count +=1
            if row_count < 5:
                continue
            user_to_time[row[0].lower()] = float(row[2])

        return user_to_time

    def get_workshop_week(self):
        self._report_csv_content.seek(0)  # Ensure pointer is at the start for re-reading
        reader = csv.reader(self._report_csv_content)

        for row_counter, row in enumerate(reader, 1):
            if row_counter == 2:
                date_str = row[2].split(" ")[0]  # This gives you '3/23/2024'
                date_obj = datetime.strptime(date_str, "%m/%d/%Y")


                return Semester.date_to_week_number(date_obj)




    def process_attendance(self, tutor):
        chosen_class = next((lang for num, lang in class_options if num == str(self.cleaned_data['class_choice'])), "Language not found")
        ignore_users = self.cleaned_data['no_participation'].split(',')
        ignore_users = [val.strip() for val in ignore_users]#strip of any extra space
        user_to_email = self.get_user_to_email()
        user_to_time = self.get_user_to_time()
        workshop_week = self.get_workshop_week()

        report = {}# we are going to return this to be able to copy and do whatever later on.
        report['emails_to_report'] = [user_to_email[key] for key in user_to_email]
        report['no_participation'] = []
        report['not_enough_time'] = []
        report['no_enrollment'] = []
        report['non_exisiting_student'] = []
        if self.cleaned_data['ignore_duration']:#incase we cut a workshop short and dont want to update time manually
            user_to_time = {key: 60 for key in user_to_time}

        for name in user_to_email:
            try:
                stu_obj = Student.objects.get(pk=user_to_email[name])
                enrolled_classes = stu_obj.get_enrolled_classes()
                enrolled_class_names = [enrolled.class_name for enrolled in enrolled_classes]#transform the obj into just the string since thats really what we are comparing
                if chosen_class in enrolled_class_names:
                    attendance_record, created = AttendanceRecord.objects.update_or_create(
                        student=stu_obj,
                        class_ref=enrolled_classes[enrolled_class_names.index(chosen_class)],#it works just trust,
                        week=workshop_week,
                        defaults={
                            'attendance_type': "Workshop",
                            'recorded_by': tutor,
                            'attended': True
                        }
                    )
                    if stu_obj.email in ignore_users:
                       attendance_record.attended = False
                       attendance_record.attendance_type = "Workshop, stripped due to participation."
                       report['no_participation'].append(f"{stu_obj.email} was stripped of attendance due to participation.")
                    
                    if user_to_time[name] < 30:
                        report['not_enough_time'].append(f"{stu_obj.email} did not get attendance, they were missing {30 - user_to_time[name]} minutes")
                        attendance_record.attendance_type = attendance_record.attendance_type + ", not enough time in workshop."
                        attendance_record.attended = False

                    attendance_record.save()
                else:
                    report['no_enrollment'].append(f"{stu_obj.email} is not enrolled in the following class: {chosen_class}")
            except Student.DoesNotExist:
                report['non_exisiting_student'].append(f"no student with the following email: {stu_obj.email}")
   
        return report             






class ImportStudentData(forms.Form):
    import_csv = forms.FileField()
    imported_class = forms.ModelChoiceField(queryset=Class.objects.all(), empty_label="Select a class.")

    def clean_import_csv(self):
        file = self.cleaned_data['import_csv']
        if not file.name.endswith('.csv'):
            raise ValidationError("Only CSV files are allowed.")
        return file
    
    def process(self):
        selected_class = self.cleaned_data.get('imported_class')
        student_group, created = Group.objects.get_or_create(name='Student')
        cleaned_file = self.cleaned_data['import_csv']
        wrapped_file = TextIOWrapper(cleaned_file.file, encoding='utf-8-sig')
        reader = csv.reader(wrapped_file)

        data_order = {}
        row_count = -1

        for row in reader:  
            row_count +=1
            if len(row) == 0:
                continue
            if row_count == 2:
                for i in range(len(row)):
                    data_order[row[i]] = i #we can use this now in the actual rows with student data
            if row_count > 2:
                email = row[data_order["Email"]].strip()
                first_name = row[data_order["First Name"]].strip()
                last_name = row[data_order["Last Name"]].strip()
                id = row[data_order["Student ID"]].strip()

                newStu, created = Student.objects.get_or_create(
                    email=email,
                    defaults={'id_number': id, 'first_name': first_name, 'last_name': last_name}
                )
                
                newUser, user_created = User.objects.get_or_create(
                    username= email,  # Using the email as the username
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'email': email
                    }   
                )

                if user_created:
                    newUser.set_password(id)
                    newUser.groups.add(student_group)
                    newUser.save()
                    print(f"User account created for {newStu.first_name} {newStu.last_name}.")

                newEnrollment, created = ClassEnrollment.objects.get_or_create(
                    student=newStu,
                    enrolled_class=selected_class
                )


