import pandas as pd
import io
import logging
from decimal import Decimal
from rest_framework import status, generics, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django_filters.rest_framework import DjangoFilterBackend
from .models import Employee, SalaryStructure, MonthlySalaryData, ActualSalaryCredited
from .serializers import (
    EmployeeSerializer, 
    SalaryStructureSerializer, 
    ExcelImportSerializer,
    MonthlySalaryDataSerializer,
    MonthlySalaryUploadSerializer
)
from departments.models import Department


class EmployeeListCreateView(generics.ListCreateAPIView):
    """
    List all employees or create a new employee.
    """
    queryset = Employee.objects.filter(is_active=True).select_related('department')
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['department', 'pay_mode', 'is_active']
    search_fields = ['name', 'employee_id', 'position', 'location']
    ordering_fields = ['name', 'employee_id', 'doj', 'created_at']
    ordering = ['name']


class EmployeeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete an employee.
    """
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated]

    def perform_destroy(self, instance):
        # Soft delete - set is_active to False
        instance.is_active = False
        instance.save()


class SalaryStructureListCreateView(generics.ListCreateAPIView):
    """
    List all salary structures or create a new one.
    """
    queryset = SalaryStructure.objects.filter(is_active=True).select_related('employee')
    serializer_class = SalaryStructureSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['employee', 'salary_type', 'is_active']
    search_fields = ['employee__name', 'employee__employee_id']


class SalaryStructureDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a salary structure.
    """
    queryset = SalaryStructure.objects.all()
    serializer_class = SalaryStructureSerializer
    permission_classes = [IsAuthenticated]

    def perform_destroy(self, instance):
        # Soft delete - set is_active to False
        instance.is_active = False
        instance.save()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def import_excel(request):
    """
    Import employees from Excel file.
    """
    serializer = ExcelImportSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    file = serializer.validated_data['file']
    
    try:
        # Read Excel file
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        
        # Validate required columns - handle different column name formats
        required_columns = [
            'employee_id', 'name', 'position', 'dob', 'doj', 'pan', 
            'bank_account', 'bank_ifsc', 'pay_mode', 'location'
        ]
        
        # Also check for alternative column names (Excel format)
        alternative_columns = [
            'Employee ID', 'Employee', 'Name', 'Position', 'Department',
            'DOB', 'DOJ', 'PAN', 'PF Number', 'Bank Account',
            'Bank IFSC', 'Pay Mode', 'Location', 'Health Card No', 'Health Card',
            'LPA', 'Is Active', 'Email', 'Mail'
        ]
        
        # Map alternative column names to standard names
        column_mapping = {
            'Employee ID': 'employee_id',
            'Employee': 'employee_id',
            'Name': 'name', 
            'Position': 'position',
            'Department': 'department_name',  # Keep as department_name for mapping
            'DOB': 'dob',
            'DOJ': 'doj',
            'PAN': 'pan',
            'PF Number': 'pf_number',
            'Bank Account': 'bank_account',
            'Bank IFSC': 'bank_ifsc',
            'Pay Mode': 'pay_mode',
            'Location': 'location',
            'Health Card No': 'health_card_no',
            'Health Card': 'health_card_no',
            'LPA': 'lpa',
            'Is Active': 'is_active',
            'Email': 'email',
            'Mail': 'email',
            'Annual CTC': 'annual_ctc'
        }
        
        # Department name to code mapping
        department_mapping = {
            'Sales': 'SALES001',
            'Finance': 'FIN001',
            'HR': 'HR001',
            'Operations': 'OPS001',
            'IT': 'IT001',
            'Marketing': 'MKT001'
        }
        
        # Rename columns to standard format
        df = df.rename(columns=column_mapping)
        
        # Check for either department_name or department_code (after renaming)
        has_department = 'department_name' in df.columns or 'department_code' in df.columns
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return Response({
                'success': False,
                'errors': [f'Missing required columns: {", ".join(missing_columns)}']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not has_department:
            return Response({
                'success': False,
                'errors': ['Missing department information. Please include either "Department" or "department_code" column.']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Process employees
        imported_count = 0
        errors = []
        warnings = []
        
        with transaction.atomic():
            for index, row in df.iterrows():
                try:
                    # Get department - handle both department_name and department_code
                    department = None
                    if 'department_name' in row and pd.notna(row['department_name']):
                        # Map department name to code
                        dept_name = str(row['department_name']).strip()
                        if dept_name in department_mapping:
                            dept_code = department_mapping[dept_name]
                            try:
                                department = Department.objects.get(
                                    department_code=dept_code,
                                    is_active=True
                                )
                            except Department.DoesNotExist:
                                errors.append(f"Row {index + 2}: Department '{dept_name}' (code: {dept_code}) not found")
                                continue
                        else:
                            errors.append(f"Row {index + 2}: Unknown department '{dept_name}'. Available: {list(department_mapping.keys())}")
                            continue
                    elif 'department_code' in row and pd.notna(row['department_code']):
                        try:
                            department = Department.objects.get(
                                department_code=row['department_code'],
                                is_active=True
                            )
                        except Department.DoesNotExist:
                            errors.append(f"Row {index + 2}: Department code '{row['department_code']}' not found")
                            continue
                    else:
                        errors.append(f"Row {index + 2}: No department specified")
                        continue
                    
                    # Check if employee already exists
                    if Employee.objects.filter(employee_id=row['employee_id']).exists():
                        warnings.append(f"Row {index + 2}: Employee ID '{row['employee_id']}' already exists")
                        continue
                    
                    # Handle date parsing with different formats
                    try:
                        # Try to parse date, handle various formats
                        dob_str = str(row['dob']).strip()
                        # Fix single digit days (e.g., 1990-05-1 -> 1990-05-01)
                        if len(dob_str.split('-')) == 3:
                            parts = dob_str.split('-')
                            if len(parts[2]) == 1:
                                parts[2] = '0' + parts[2]
                            dob_str = '-'.join(parts)
                        dob = pd.to_datetime(dob_str).date()
                    except:
                        errors.append(f"Row {index + 2}: Invalid DOB format '{row['dob']}'. Expected format: YYYY-MM-DD")
                        continue
                        
                    try:
                        # Try to parse date, handle various formats
                        doj_str = str(row['doj']).strip()
                        # Fix single digit days (e.g., 2020-01-1 -> 2020-01-01)
                        if len(doj_str.split('-')) == 3:
                            parts = doj_str.split('-')
                            if len(parts[2]) == 1:
                                parts[2] = '0' + parts[2]
                            doj_str = '-'.join(parts)
                        doj = pd.to_datetime(doj_str).date()
                    except:
                        errors.append(f"Row {index + 2}: Invalid DOJ format '{row['doj']}'. Expected format: YYYY-MM-DD")
                        continue
                    
                    # Handle LPA field
                    lpa_value = None
                    if 'lpa' in row and pd.notna(row['lpa']):
                        try:
                            lpa_value = float(row['lpa'])
                        except (ValueError, TypeError):
                            warnings.append(f"Row {index + 2}: Invalid LPA value '{row['lpa']}'")
                    
                    # Clean data fields
                    pan_clean = str(row['pan']).strip().replace(':', '').replace(' ', '')
                    bank_account_clean = str(row['bank_account']).strip().replace(':', '').replace(' ', '')
                    position_clean = str(row['position']).strip().replace(':', '').replace(' ', ' ')
                    
                    # Create employee
                    employee = Employee.objects.create(
                        employee_id=row['employee_id'],
                        name=row['name'],
                        position=position_clean,
                        department=department,
                        dob=dob,
                        doj=doj,
                        pan=pan_clean,
                        pf_number=row['pf_number'],
                        bank_account=bank_account_clean,
                        bank_ifsc=row['bank_ifsc'],
                        pay_mode=row['pay_mode'],
                        location=row['location'],
                        health_card_no=row.get('health_card_no', ''),
                        email=row.get('email', None),
                        lpa=lpa_value,
                        is_active=row.get('is_active', True) if 'is_active' in row else True
                    )
                    
                    # Create salary structure if annual_ctc is provided
                    if 'annual_ctc' in row and pd.notna(row['annual_ctc']):
                        try:
                            annual_ctc = float(row['annual_ctc'])
                            SalaryStructure.objects.create(
                                employee=employee,
                                salary_type='SALARY',
                                annual_ctc=annual_ctc,
                                is_active=True
                            )
                        except (ValueError, TypeError):
                            warnings.append(f"Row {index + 2}: Invalid annual_ctc value '{row['annual_ctc']}'")
                    
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {index + 2}: {str(e)}")
                    continue
        
        return Response({
            'success': True,
            'imported_count': imported_count,
            'errors': errors,
            'warnings': warnings
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'errors': [f'Error processing file: {str(e)}']
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def employee_stats(request):
    """
    Get employee statistics.
    """
    total_employees = Employee.objects.filter(is_active=True).count()
    employees_by_department = {}
    employees_by_pay_mode = {}
    
    # Count by department
    for dept in Department.objects.filter(is_active=True):
        count = Employee.objects.filter(department=dept, is_active=True).count()
        if count > 0:
            employees_by_department[dept.department_name] = count
    
    # Count by pay mode
    for pay_mode, _ in Employee.PAY_MODE_CHOICES:
        count = Employee.objects.filter(pay_mode=pay_mode, is_active=True).count()
        if count > 0:
            employees_by_pay_mode[pay_mode] = count
    
    return Response({
        'success': True,
        'data': {
            'total_employees': total_employees,
            'by_department': employees_by_department,
            'by_pay_mode': employees_by_pay_mode
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_employees_by_department(request, department_id):
    """
    Get employees by department.
    """
    try:
        department = Department.objects.get(id=department_id, is_active=True)
        employees = Employee.objects.filter(
            department=department,
            is_active=True
        ).select_related('department')
        
        serializer = EmployeeSerializer(employees, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Department.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Department not found'
        }, status=status.HTTP_404_NOT_FOUND)


class MonthlySalaryDataListView(generics.ListAPIView):
    """
    List monthly salary data.
    """
    queryset = MonthlySalaryData.objects.all().select_related('employee', 'uploaded_by')
    serializer_class = MonthlySalaryDataSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['employee', 'month', 'year']
    search_fields = ['employee__name', 'employee__employee_id']
    ordering_fields = ['month', 'year', 'uploaded_at']
    ordering = ['-year', '-month']


class MonthlySalaryDataDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete monthly salary data.
    """
    queryset = MonthlySalaryData.objects.all()
    serializer_class = MonthlySalaryDataSerializer
    permission_classes = [IsAuthenticated]


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def upload_monthly_salary_excel(request):
    """
    Upload monthly salary data from Excel file.
    """
    serializer = MonthlySalaryUploadSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    file = serializer.validated_data['file']
    month = serializer.validated_data['month']
    year = serializer.validated_data['year']
    
    try:
        # Read Excel file
        df = pd.read_excel(file)
        
        # Validate required columns
        required_columns = [
            'employee_id', 'basic', 'hra', 'da', 'conveyance', 'medical', 
            'special_allowance', 'pf_employee', 'professional_tax', 'pf_employer',
            'work_days', 'days_in_month'
        ]
        
        # Also check for alternative column names
        column_mapping = {
            'Employee ID': 'employee_id',
            'Employee': 'employee_id',
            'Basic': 'basic',
            'Basic Salary': 'basic',
            'HRA': 'hra',
            'House Rent Allowance': 'hra',
            'DA': 'da',
            'Dearness Allowance': 'da',
            'Conveyance': 'conveyance',
            'Conveyance Allowance': 'conveyance',
            'Medical': 'medical',
            'Medical Allowance': 'medical',
            'Special Allowance': 'special_allowance',
            'Special': 'special_allowance',
            'PF Employee': 'pf_employee',
            'PF (Employee)': 'pf_employee',
            'Professional Tax': 'professional_tax',
            'PT': 'professional_tax',
            'PF Employer': 'pf_employer',
            'PF (Employer)': 'pf_employer',
            'Work Days': 'work_days',
            'Working Days': 'work_days',
            'Days in Month': 'days_in_month',
            'Total Days': 'days_in_month',
            'LOP Days': 'lop_days',
            'Loss of Pay': 'lop_days',
            'Other Deductions': 'other_deductions',
            'Salary Advance': 'salary_advance'
        }
        
        # Rename columns to standard format
        df = df.rename(columns=column_mapping)
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return Response({
                'success': False,
                'errors': [f'Missing required columns: {", ".join(missing_columns)}']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Process salary data
        imported_count = 0
        updated_count = 0
        errors = []
        warnings = []
        
        with transaction.atomic():
            for index, row in df.iterrows():
                try:
                    # Get employee
                    try:
                        employee = Employee.objects.get(
                            employee_id=row['employee_id'],
                            is_active=True
                        )
                    except Employee.DoesNotExist:
                        errors.append(f"Row {index + 2}: Employee ID '{row['employee_id']}' not found")
                        continue
                    
                    # Prepare salary data
                    salary_data = {
                        'employee': employee,
                        'month': month,
                        'year': year,
                        'basic': Decimal(str(row['basic'])) if pd.notna(row['basic']) else Decimal('0'),
                        'hra': Decimal(str(row['hra'])) if pd.notna(row['hra']) else Decimal('0'),
                        'da': Decimal(str(row['da'])) if pd.notna(row['da']) else Decimal('0'),
                        'conveyance': Decimal(str(row['conveyance'])) if pd.notna(row['conveyance']) else Decimal('0'),
                        'medical': Decimal(str(row['medical'])) if pd.notna(row['medical']) else Decimal('0'),
                        'special_allowance': Decimal(str(row['special_allowance'])) if pd.notna(row['special_allowance']) else Decimal('0'),
                        'pf_employee': Decimal(str(row['pf_employee'])) if pd.notna(row['pf_employee']) else Decimal('0'),
                        'professional_tax': Decimal(str(row['professional_tax'])) if pd.notna(row['professional_tax']) else Decimal('0'),
                        'pf_employer': Decimal(str(row['pf_employer'])) if pd.notna(row['pf_employer']) else Decimal('0'),
                        'other_deductions': Decimal(str(row.get('other_deductions', 0))) if pd.notna(row.get('other_deductions', 0)) else Decimal('0'),
                        'salary_advance': Decimal(str(row.get('salary_advance', 0))) if pd.notna(row.get('salary_advance', 0)) else Decimal('0'),
                        'work_days': int(row['work_days']) if pd.notna(row['work_days']) else 0,
                        'days_in_month': int(row['days_in_month']) if pd.notna(row['days_in_month']) else 0,
                        'lop_days': int(row.get('lop_days', 0)) if pd.notna(row.get('lop_days', 0)) else 0,
                        'uploaded_by': request.user
                    }
                    
                    # Check if salary data already exists for this employee and month
                    existing_salary = MonthlySalaryData.objects.filter(
                        employee=employee,
                        month=month,
                        year=year
                    ).first()
                    
                    if existing_salary:
                        # Update existing record
                        for key, value in salary_data.items():
                            if key != 'employee':  # Don't update employee field
                                setattr(existing_salary, key, value)
                        existing_salary.save()
                        updated_count += 1
                    else:
                        # Create new record
                        MonthlySalaryData.objects.create(**salary_data)
                        imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {index + 2}: {str(e)}")
                    continue
        
        return Response({
            'success': True,
            'imported_count': imported_count,
            'updated_count': updated_count,
            'errors': errors,
            'warnings': warnings
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'errors': [f'Error processing file: {str(e)}']
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_monthly_salary_data(request, month, year):
    """
    Get monthly salary data for a specific month and year.
    """
    try:
        salary_data = MonthlySalaryData.objects.filter(
            month=month,
            year=year
        ).select_related('employee', 'uploaded_by')
        
        serializer = MonthlySalaryDataSerializer(salary_data, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error retrieving data: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def monthly_salary_stats(request):
    """
    Get monthly salary data statistics.
    """
    try:
        total_records = MonthlySalaryData.objects.count()
        records_by_month = {}
        records_by_year = {}
        
        # Count by month
        for record in MonthlySalaryData.objects.all():
            month_key = f"{record.month} {record.year}"
            records_by_month[month_key] = records_by_month.get(month_key, 0) + 1
        
        # Count by year
        for record in MonthlySalaryData.objects.all():
            records_by_year[record.year] = records_by_year.get(record.year, 0) + 1
        
        return Response({
            'success': True,
            'data': {
                'total_records': total_records,
                'by_month': records_by_month,
                'by_year': records_by_year
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error getting statistics: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_salary_calculation_preview(request):
    """
    Get salary calculation preview for selected employees and month.
    """
    try:
        employee_ids = request.GET.getlist('employee_ids')
        month = request.GET.get('month')
        year = int(request.GET.get('year'))
        
        if not employee_ids or not month or not year:
            return Response({
                'success': False,
                'message': 'Employee IDs, month, and year are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        employees = Employee.objects.filter(
            id__in=employee_ids,
            is_active=True
        ).select_related('department')
        
        preview_data = []
        
        for employee in employees:
            # Get monthly salary data
            monthly_salary = MonthlySalaryData.objects.filter(
                employee=employee,
                month=month,
                year=year
            ).first()
            
            if employee.lpa and monthly_salary:
                # Use LPA from employee model (convert to annual amount)
                lpa_annual = float(employee.lpa) * 100000  # Convert lakhs to rupees
                calculated_monthly = float(monthly_salary.net_pay)
                
                preview_data.append({
                    'employee_id': employee.id,
                    'employee_name': employee.name,
                    'employee_id_code': employee.employee_id,
                    'department': employee.department.department_name,
                    'lpa': float(employee.lpa),
                    'calculated_monthly': calculated_monthly,
                    'lpa_monthly': lpa_annual / 12,
                    'difference': abs(calculated_monthly - (lpa_annual / 12)),
                    'difference_percentage': abs((calculated_monthly - (lpa_annual / 12)) / (lpa_annual / 12) * 100) if lpa_annual > 0 else 0,
                    'is_nearby': abs(calculated_monthly - (lpa_annual / 12)) <= (lpa_annual / 12 * 0.1)  # Within 10%
                })
        
        return Response({
            'success': True,
            'data': preview_data,
            'summary': {
                'total_employees': len(preview_data),
                'nearby_calculations': len([emp for emp in preview_data if emp['is_nearby']]),
                'month': month,
                'year': year
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error getting salary preview: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def upload_actual_salary_credited(request):
    """
    Upload actual salary credited data for employees.
    """
    try:
        data = request.data
        employee_salaries = data.get('employee_salaries', [])
        month = data.get('month')
        year = int(data.get('year'))
        
        if not employee_salaries or not month or not year:
            return Response({
                'success': False,
                'message': 'Employee salaries, month, and year are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_count = 0
        updated_count = 0
        errors = []
        
        for salary_data in employee_salaries:
            try:
                employee_id = salary_data.get('employee_id')
                actual_salary = Decimal(str(salary_data.get('actual_salary_credited', 0)))
                
                if not employee_id or actual_salary <= 0:
                    errors.append(f"Invalid data for employee {employee_id}")
                    continue
                
                employee = Employee.objects.get(id=employee_id)
                
                # Check if actual salary already exists
                existing_salary = ActualSalaryCredited.objects.filter(
                    employee=employee,
                    month=month,
                    year=year
                ).first()
                
                if existing_salary:
                    # Update existing record
                    existing_salary.actual_salary_credited = actual_salary
                    existing_salary.uploaded_by = request.user
                    existing_salary.save()
                    updated_count += 1
                else:
                    # Create new record
                    ActualSalaryCredited.objects.create(
                        employee=employee,
                        month=month,
                        year=year,
                        actual_salary_credited=actual_salary,
                        uploaded_by=request.user
                    )
                    uploaded_count += 1
                    
            except Employee.DoesNotExist:
                errors.append(f"Employee with ID {employee_id} not found")
            except Exception as e:
                errors.append(f"Error processing employee {employee_id}: {str(e)}")
        
        return Response({
            'success': True,
            'uploaded_count': uploaded_count,
            'updated_count': updated_count,
            'errors': errors
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error uploading actual salary data: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_actual_salary_credited(request):
    """
    Get actual salary credited data for employees.
    """
    try:
        month = request.GET.get('month')
        year = int(request.GET.get('year')) if request.GET.get('year') else None
        employee_id = request.GET.get('employee_id')
        
        queryset = ActualSalaryCredited.objects.select_related('employee', 'uploaded_by')
        
        if month:
            queryset = queryset.filter(month=month)
        if year:
            queryset = queryset.filter(year=year)
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        data = []
        for record in queryset:
            data.append({
                'id': record.id,
                'employee_id': record.employee.id,
                'employee_name': record.employee.name,
                'employee_id_code': record.employee.employee_id,
                'month': record.month,
                'year': record.year,
                'actual_salary_credited': float(record.actual_salary_credited),
                'uploaded_at': record.uploaded_at,
                'uploaded_by': record.uploaded_by.username
            })
        
        return Response({
            'success': True,
            'data': data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error getting actual salary data: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)