from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import Department
from .serializers import DepartmentSerializer


@method_decorator(csrf_exempt, name='dispatch')
class DepartmentListCreateView(generics.ListCreateAPIView):
    """
    List all departments or create a new department.
    """
    queryset = Department.objects.filter(is_active=True)
    serializer_class = DepartmentSerializer
    permission_classes = [AllowAny]  # Temporarily allow unauthenticated access for testing


@method_decorator(csrf_exempt, name='dispatch')
class DepartmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a department.
    """
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]

    def perform_destroy(self, instance):
        # Soft delete - set is_active to False
        instance.is_active = False
        instance.save()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def department_stats(request):
    """
    Get department statistics.
    """
    departments = Department.objects.filter(is_active=True)
    
    stats = []
    for dept in departments:
        stats.append({
            'id': dept.id,
            'name': dept.department_name,
            'code': dept.department_code,
            'employee_count': dept.employee_count,
            'created_at': dept.created_at
        })
    
    return Response({
        'success': True,
        'data': stats
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def check_departments(request):
    """
    Check if departments exist in the database.
    """
    try:
        total_departments = Department.objects.count()
        active_departments = Department.objects.filter(is_active=True).count()
        
        departments = Department.objects.filter(is_active=True)
        dept_list = []
        for dept in departments:
            dept_list.append({
                'id': dept.id,
                'code': dept.department_code,
                'name': dept.department_name,
                'is_active': dept.is_active
            })
        
        return Response({
            'success': True,
            'total_departments': total_departments,
            'active_departments': active_departments,
            'departments': dept_list
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def create_sample_departments_api(request):
    """
    Create sample departments via API.
    """
    try:
        departments_data = [
            {'department_code': 'IT', 'department_name': 'Information Technology', 'description': 'Software development and IT support'},
            {'department_code': 'HR', 'department_name': 'Human Resources', 'description': 'Human resources and employee management'},
            {'department_code': 'FIN', 'department_name': 'Finance', 'description': 'Financial management and accounting'},
            {'department_code': 'MKT', 'department_name': 'Marketing', 'description': 'Marketing and business development'},
            {'department_code': 'OPS', 'department_name': 'Operations', 'description': 'Operations and project management'},
            {'department_code': 'SALES', 'department_name': 'Sales', 'description': 'Sales and customer relations'},
        ]
        
        created_count = 0
        created_departments = []
        
        for dept_data in departments_data:
            department, created = Department.objects.get_or_create(
                department_code=dept_data['department_code'],
                defaults={
                    'department_name': dept_data['department_name'],
                    'description': dept_data['description'],
                    'is_active': True
                }
            )
            if created:
                created_count += 1
                created_departments.append({
                    'id': department.id,
                    'code': department.department_code,
                    'name': department.department_name
                })
        
        return Response({
            'success': True,
            'message': f'Created {created_count} new departments',
            'created_departments': created_departments,
            'total_departments': Department.objects.filter(is_active=True).count()
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)