from django import template
from ..models import Semester
from datetime import datetime

register = template.Library()

@register.simple_tag
def get_week_attendance(student, week, class_pk):
    return student.get_attendance_for_week(week, class_pk)


@register.filter
def week_number_to_date(week):
    date = Semester.week_number_to_date(week)
    
    return str(date.strftime('%m/%d/%Y'))

@register.filter
def today_to_week(x):
    return Semester.date_to_week_number(datetime.now())