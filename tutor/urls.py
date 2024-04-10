from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home , name='home'),
    path('semesterData', views.handle_semester_data , name='semester_data'),
    path('tutor/login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/',
        auth_views.LogoutView.as_view(),
        name = 'logout'
    ),
    path('update-attendance/', views.update_attendance, name="update-attendance"),
    path('clearsemester', views.clear_semester_data, name="clearsemester"),
]