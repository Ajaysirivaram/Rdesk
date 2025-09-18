import pandas as pd
import io
import logging
from decimal import Decimal
from rest_framework import status, generics, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction, models
from django.views.decorators.csrf import csrf_exempt
from django_filters.rest_framework import DjangoFilterBackend
from .models import Employee, SalaryStructure, MonthlySalaryData, ActualSalaryCredited, EmailLog
from .serializers import (
    EmployeeSerializer, 
    SalaryStructureSerializer, 
    ExcelImportSerializer,
    MonthlySalaryDataSerializer,
    MonthlySalaryUploadSerializer
)
from .email_service import EmployeeEmailService
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
                        personal_email=row.get('personal_email', None),  # Add personal email field
                        password=row.get('password', None),  # Add password field
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
                    
                    # Send welcome email if both personal_email and password are provided
                    if employee.personal_email and employee.password:
                        try:
                            email_service = EmployeeEmailService()
                            success, message = email_service.send_welcome_email(employee)
                            
                            if not success:
                                warnings.append(f"Row {index + 2}: Failed to send welcome email to {employee.personal_email}: {message}")
                        except Exception as email_error:
                            warnings.append(f"Row {index + 2}: Error sending welcome email: {str(email_error)}")
                    
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


class MonthlySalaryDataListView(generics.ListCreateAPIView):
    """
    List and create monthly salary data.
    """
    queryset = MonthlySalaryData.objects.all().select_related('employee', 'uploaded_by')
    serializer_class = MonthlySalaryDataSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['employee', 'month', 'year']
    search_fields = ['employee__name', 'employee__employee_id']
    ordering_fields = ['month', 'year', 'uploaded_at']
    ordering = ['-year', '-month']
    
    def perform_create(self, serializer):
        """
        Set the uploaded_by field to the current user.
        """
        serializer.save(uploaded_by=self.request.user)


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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_welcome_email(request, pk):
    """
    Send welcome email to specific employee.
    """
    try:
        employee = get_object_or_404(Employee, pk=pk)
        
        if not employee.personal_email:
            return Response({
                'success': False,
                'message': 'Employee has no personal email address'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not employee.password:
            return Response({
                'success': False,
                'message': 'Employee has no password set'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        email_service = EmployeeEmailService()
        success, message = email_service.send_welcome_email(employee)
        
        return Response({
            'success': success,
            'message': message
        }, status=status.HTTP_200_OK if success else status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_bulk_welcome_emails(request):
    """
    Send welcome emails to multiple employees.
    """
    try:
        employee_ids = request.data.get('employee_ids', [])
        if not employee_ids:
            return Response({
                'success': False,
                'message': 'No employee IDs provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get employees
        employees = Employee.objects.filter(
            id__in=employee_ids,
            is_active=True,
            personal_email__isnull=False,
            password__isnull=False
        ).exclude(personal_email='').exclude(password='')
        
        if not employees.exists():
            return Response({
                'success': False,
                'message': 'No valid employees found with email and password'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        email_service = EmployeeEmailService()
        results = email_service.send_bulk_welcome_emails(employees)
        
        return Response({
            'success': True,
            'message': f'Bulk welcome emails processed. Sent: {results["sent"]}, Failed: {results["failed"]}',
            'results': results
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_welcome_email_with_credentials(request, pk):
    """
    Send welcome email to employee with custom credentials.
    """
    try:
        employee = get_object_or_404(Employee, pk=pk)
        
        # Get custom credentials from request
        custom_email = request.data.get('personal_email', employee.personal_email)
        custom_password = request.data.get('password', employee.password)
        
        if not custom_email:
            return Response({
                'success': False,
                'message': 'No email address provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not custom_password:
            return Response({
                'success': False,
                'message': 'No password provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create temporary employee object with custom credentials
        temp_employee = Employee(
            name=employee.name,
            email=employee.email,
            personal_email=custom_email,
            password=custom_password,
            employee_id=employee.employee_id
        )
        
        email_service = EmployeeEmailService()
        success, message = email_service.send_welcome_email(temp_employee)
        
        return Response({
            'success': success,
            'message': message
        }, status=status.HTTP_200_OK if success else status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_employees_for_welcome_email(request):
    """
    Get list of employees who can receive welcome emails.
    """
    try:
        # Get employees without personal email or password
        employees_missing_info = Employee.objects.filter(
            is_active=True
        ).filter(
            models.Q(personal_email__isnull=True) | 
            models.Q(personal_email='') | 
            models.Q(password__isnull=True) | 
            models.Q(password='')
        ).select_related('department')
        
        # Get employees with complete info
        employees_ready = Employee.objects.filter(
            is_active=True,
            personal_email__isnull=False,
            password__isnull=False
        ).exclude(personal_email='').exclude(password='').select_related('department')
        
        # Serialize data
        missing_serializer = EmployeeSerializer(employees_missing_info, many=True)
        ready_serializer = EmployeeSerializer(employees_ready, many=True)
        
        return Response({
            'success': True,
            'employees_ready': ready_serializer.data,
            'employees_missing_info': missing_serializer.data,
            'counts': {
                'ready': employees_ready.count(),
                'missing_info': employees_missing_info.count()
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_email_logs(request):
    """
    Get email sending logs with optional filtering.
    """
    try:
        # Get query parameters
        email_type = request.GET.get('email_type')
        status_filter = request.GET.get('status')
        employee_id = request.GET.get('employee_id')
        limit = int(request.GET.get('limit', 50))
        
        # Build queryset
        queryset = EmailLog.objects.all().select_related('employee')
        
        if email_type:
            queryset = queryset.filter(email_type=email_type)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        # Order by most recent first and limit results
        queryset = queryset.order_by('-sent_at')[:limit]
        
        # Serialize data
        logs_data = []
        for log in queryset:
            logs_data.append({
                'id': log.id,
                'employee_id': log.employee.employee_id if log.employee else None,
                'employee_name': log.employee.name if log.employee else 'N/A',
                'email_type': log.email_type,
                'recipient_email': log.recipient_email,
                'subject': log.subject,
                'status': log.status,
                'message': log.message,
                'sent_at': log.sent_at.isoformat(),
                'error_message': log.error_message
            })
        
        return Response({
            'success': True,
            'logs': logs_data,
            'count': len(logs_data)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])  # Temporarily allow any for testing
@csrf_exempt
def process_welcome_email_excel(request):
    """
    Process Excel file for welcome email sending.
    """
    try:
        # Check if it's a file upload or manual form submission
        if 'file' in request.FILES:
            # File upload processing
            file = request.FILES['file']
            
            # Read Excel file
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
        else:
            # Manual form processing - create a single-row DataFrame
            manual_data = {
                'name': request.data.get('name', ''),
                'personal_email': request.data.get('personal_email', ''),
                'password': request.data.get('password', ''),
                'system_email': request.data.get('system_email', '')
            }
            df = pd.DataFrame([manual_data])
        
        # Validate required columns
        required_columns = ['name', 'personal_email', 'password', 'system_email']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return Response({
                'success': False,
                'message': f'Missing required columns: {", ".join(missing_columns)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Process each row
        processed_count = 0
        emails_sent = 0
        errors = []
        
        email_service = EmployeeEmailService()
        
        for index, row in df.iterrows():
            try:
                # Find or create employee
                employee = None
                
                # First try to find by system_email
                if 'system_email' in row and pd.notna(row['system_email']):
                    try:
                        employee = Employee.objects.get(email=row['system_email'])
                    except Employee.DoesNotExist:
                        pass
                
                # If not found, try to find by personal_email
                if not employee and 'personal_email' in row and pd.notna(row['personal_email']):
                    try:
                        employee = Employee.objects.get(personal_email=row['personal_email'])
                    except Employee.DoesNotExist:
                        pass
                
                # If still not found, create a new employee
                if not employee:
                    # Validate required fields for new employee
                    if not all(pd.notna(row.get(field, '')) for field in ['name', 'system_email', 'personal_email', 'password']):
                        errors.append(f"Row {index + 1}: Missing required fields for new employee creation")
                        continue
                    
                    # Create new employee with all required fields
                    from datetime import date
                    from departments.models import Department
                    
                    # Get default department (first available)
                    default_department = Department.objects.first()
                    if not default_department:
                        errors.append(f"Row {index + 1}: No departments available. Please create a department first.")
                        continue
                    
                    # Generate unique employee ID
                    def generate_unique_employee_id():
                        counter = 1
                        while True:
                            new_id = f"NEW{counter:03d}"
                            if not Employee.objects.filter(employee_id=new_id).exists():
                                return new_id
                            counter += 1
                            if counter > 999:  # Safety limit
                                return f"NEW{int(time.time())}"  # Fallback to timestamp
                    
                    import time
                    unique_employee_id = generate_unique_employee_id()
                    
                    employee = Employee.objects.create(
                        # Basic Information
                        employee_id=unique_employee_id,
                        name=row['name'].strip(),
                        position='New Employee',  # Default position
                        department=default_department,
                        
                        # Personal Information
                        dob=date(1990, 1, 1),  # Default DOB - should be updated later
                        doj=date.today(),  # Date of joining = today
                        
                        # Financial Information
                        pan='ABCDE1234F',  # Default PAN - should be updated later
                        bank_account='1234567890',  # Default bank account - should be updated later
                        bank_ifsc='ABCD0123456',  # Default IFSC - should be updated later
                        pay_mode='NEFT',
                        
                        # Additional Information
                        location='Office',  # Default location
                        
                        # Email and Login
                        email=row['system_email'].strip(),
                        personal_email=row['personal_email'].strip(),
                        password=row['password'].strip(),
                        
                        # Salary Information
                        lpa=0,  # Default salary - should be updated later
                    )
                    print(f"Created new employee: {employee.name} ({employee.email})")
                
                # Update employee with new credentials
                if 'personal_email' in row and pd.notna(row['personal_email']):
                    employee.personal_email = row['personal_email']
                if 'password' in row and pd.notna(row['password']):
                    employee.password = row['password']
                if 'system_email' in row and pd.notna(row['system_email']):
                    employee.email = row['system_email']
                
                employee.save()
                
                # Send welcome email
                success, message = email_service.send_welcome_email(employee)
                
                if success:
                    emails_sent += 1
                else:
                    errors.append(f"Row {index + 1}: {message}")
                
                processed_count += 1
                
            except Exception as e:
                errors.append(f"Row {index + 1}: {str(e)}")
        
        return Response({
            'success': True,
            'message': f'Processed {processed_count} employees, sent {emails_sent} welcome emails',
            'processed_count': processed_count,
            'emails_sent': emails_sent,
            'new_employees_created': processed_count - len([e for e in errors if 'not found' not in e]),
            'errors': errors
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error processing file: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def test_welcome_email_simple(request):
    """
    Simple test endpoint for welcome email without authentication
    """
    try:
        manual_data = {
            'name': request.data.get('name', 'Test User'),
            'personal_email': request.data.get('personal_email', 'test@example.com'),
            'password': request.data.get('password', 'TestPass123!'),
            'system_email': request.data.get('system_email', 'test@camelq.co.in')
        }
        
        # Create test employee object
        class TestEmployee:
            def __init__(self, name, email, personal_email, password, employee_id):
                self.name = name
                self.email = email
                self.personal_email = personal_email
                self.password = password
                self.employee_id = employee_id
        
        test_employee = TestEmployee(
            name=manual_data['name'],
            email=manual_data['system_email'],
            personal_email=manual_data['personal_email'],
            password=manual_data['password'],
            employee_id='TEST001'
        )
        
        # Send email
        email_service = EmployeeEmailService()
        success, message = email_service.send_welcome_email(test_employee)
        
        return Response({
            'success': success,
            'message': message,
            'test_data': manual_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_email_logging(request):
    """
    Test endpoint to check if email logging is working.
    """
    try:
        # Create a test email log entry
        test_log = EmailLog.objects.create(
            employee=None,
            email_type='WELCOME',
            recipient_email='test@example.com',
            subject='Test Email Log',
            status='SENT',
            message='This is a test email log entry'
        )
        
        # Get total email logs count
        total_logs = EmailLog.objects.count()
        
        return Response({
            'success': True,
            'message': 'Email logging test successful',
            'test_log_id': test_log.id,
            'total_logs': total_logs
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Email logging test failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)