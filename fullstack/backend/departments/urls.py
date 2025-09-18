from django.urls import path
from . import views

app_name = 'departments'

urlpatterns = [
    path('', views.DepartmentListCreateView.as_view(), name='department-list-create'),
    path('<int:pk>/', views.DepartmentDetailView.as_view(), name='department-detail'),
    path('stats/', views.department_stats, name='department-stats'),
    path('check/', views.check_departments, name='check-departments'),
    path('create-sample/', views.create_sample_departments_api, name='create-sample-departments'),
]
