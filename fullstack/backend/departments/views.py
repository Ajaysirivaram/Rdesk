from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
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
    permission_classes = [IsAuthenticated]


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