from rest_framework import serializers
from .models import Employee, SalaryStructure, MonthlySalaryData
from departments.models import Department


class DepartmentSerializer(serializers.ModelSerializer):
    """
    Simple department serializer for employee views.
    """
    class Meta:
        model = Department
        fields = ['id', 'department_code', 'department_name']


class EmployeeSerializer(serializers.ModelSerializer):
    """
    Serializer for Employee model.
    """
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Employee
        fields = [
            'id',
            'employee_id',
            'name',
            'position',
            'department',
            'department_id',
            'dob',
            'doj',
            'pan',
            'pf_number',
            'bank_account',
            'bank_ifsc',
            'pay_mode',
            'location',
            'health_card_no',
            'email',
            'personal_email',
            'password',
            'password_changed',
            'password_set_date',
            'lpa',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'password_changed', 'password_set_date', 'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True},  # Don't return password in API responses
        }
    
    def validate_employee_id(self, value):
        """
        Validate employee ID uniqueness.
        """
        if self.instance:
            # For updates, exclude current instance
            if Employee.objects.filter(employee_id=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("Employee ID already exists.")
        else:
            # For creates, check if ID exists
            if Employee.objects.filter(employee_id=value).exists():
                raise serializers.ValidationError("Employee ID already exists.")
        
        return value.upper()
    
    def validate_department_id(self, value):
        """
        Validate department exists and is active.
        """
        try:
            department = Department.objects.get(id=value, is_active=True)
        except Department.DoesNotExist:
            raise serializers.ValidationError("Invalid department ID.")
        
        return value
    
    def create(self, validated_data):
        """
        Create employee with department and send welcome email if credentials provided.
        """
        department_id = validated_data.pop('department_id')
        department = Department.objects.get(id=department_id)
        validated_data['department'] = department
        
        # Create employee
        employee = super().create(validated_data)
        
        # Send welcome email if both personal_email and password are provided
        if employee.personal_email and employee.password:
            try:
                from .email_service import EmployeeEmailService
                email_service = EmployeeEmailService()
                success, message = email_service.send_welcome_email(employee)
                
                if success:
                    import logging
                    logging.getLogger('employees').info(f"Welcome email sent to {employee.personal_email}")
                else:
                    import logging
                    logging.getLogger('employees').warning(f"Failed to send welcome email to {employee.personal_email}: {message}")
            except Exception as e:
                import logging
                logging.getLogger('employees').error(f"Error sending welcome email: {str(e)}")
        
        return employee
    
    def update(self, instance, validated_data):
        """
        Update employee with department.
        """
        if 'department_id' in validated_data:
            department_id = validated_data.pop('department_id')
            department = Department.objects.get(id=department_id)
            validated_data['department'] = department
        return super().update(instance, validated_data)


class SalaryStructureSerializer(serializers.ModelSerializer):
    """
    Serializer for SalaryStructure model.
    """
    employee_name = serializers.CharField(source='employee.name', read_only=True)
    employee_id = serializers.CharField(source='employee.employee_id', read_only=True)
    monthly_salary = serializers.ReadOnlyField()
    basic_salary = serializers.ReadOnlyField()
    hra = serializers.ReadOnlyField()
    da = serializers.ReadOnlyField()
    conveyance = serializers.ReadOnlyField()
    medical = serializers.ReadOnlyField()
    pf_employee = serializers.ReadOnlyField()
    pf_employer = serializers.ReadOnlyField()
    professional_tax = serializers.ReadOnlyField()
    special_allowance = serializers.ReadOnlyField()
    
    class Meta:
        model = SalaryStructure
        fields = [
            'id',
            'employee',
            'employee_name',
            'employee_id',
            'salary_type',
            'annual_ctc',
            'effective_from',
            'is_active',
            'monthly_salary',
            'basic_salary',
            'hra',
            'da',
            'conveyance',
            'medical',
            'pf_employee',
            'pf_employer',
            'professional_tax',
            'special_allowance',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_employee(self, value):
        """
        Validate employee exists and is active.
        """
        if not value.is_active:
            raise serializers.ValidationError("Employee is not active.")
        return value


class ExcelImportSerializer(serializers.Serializer):
    """
    Serializer for Excel import validation.
    """
    file = serializers.FileField()
    
    def validate_file(self, value):
        """
        Validate uploaded file.
        """
        if not value.name.endswith(('.xlsx', '.xls', '.csv')):
            raise serializers.ValidationError("File must be an Excel (.xlsx, .xls) or CSV file.")
        
        if value.size > 10 * 1024 * 1024:  # 10MB limit
            raise serializers.ValidationError("File size must be less than 10MB.")
        
        return value


class MonthlySalaryDataSerializer(serializers.ModelSerializer):
    """
    Serializer for MonthlySalaryData model.
    """
    employee_name = serializers.CharField(source='employee.name', read_only=True)
    employee_id = serializers.CharField(source='employee.employee_id', read_only=True)
    total_earnings = serializers.ReadOnlyField()
    total_deductions = serializers.ReadOnlyField()
    net_pay = serializers.ReadOnlyField()
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True)
    
    class Meta:
        model = MonthlySalaryData
        fields = [
            'id',
            'employee',
            'employee_name',
            'employee_id',
            'month',
            'year',
            'basic',
            'hra',
            'da',
            'conveyance',
            'medical',
            'special_allowance',
            'pf_employee',
            'professional_tax',
            'pf_employer',
            'other_deductions',
            'salary_advance',
            'work_days',
            'days_in_month',
            'lop_days',
            'total_earnings',
            'total_deductions',
            'net_pay',
            'uploaded_at',
            'uploaded_by',
            'uploaded_by_name'
        ]
        read_only_fields = ['id', 'uploaded_at', 'uploaded_by']
    
    def validate_employee(self, value):
        """
        Validate employee exists and is active.
        """
        if not value.is_active:
            raise serializers.ValidationError("Employee is not active.")
        return value
    
    def validate(self, data):
        """
        Validate the salary data.
        """
        # Validate month format
        valid_months = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        if data.get('month') not in valid_months:
            raise serializers.ValidationError("Invalid month. Must be a full month name.")
        
        # Validate year
        if data.get('year') < 2020 or data.get('year') > 2030:
            raise serializers.ValidationError("Year must be between 2020 and 2030.")
        
        # Validate work days
        if data.get('work_days', 0) > data.get('days_in_month', 31):
            raise serializers.ValidationError("Work days cannot exceed days in month.")
        
        return data


class MonthlySalaryUploadSerializer(serializers.Serializer):
    """
    Serializer for monthly salary Excel upload.
    """
    file = serializers.FileField()
    month = serializers.CharField(max_length=20)
    year = serializers.IntegerField()
    
    def validate_file(self, value):
        """
        Validate uploaded file.
        """
        if not value.name.endswith(('.xlsx', '.xls')):
            raise serializers.ValidationError("File must be an Excel (.xlsx, .xls) file.")
        
        if value.size > 10 * 1024 * 1024:  # 10MB limit
            raise serializers.ValidationError("File size must be less than 10MB.")
        
        return value
    
    def validate_month(self, value):
        """
        Validate month format.
        """
        valid_months = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        if value not in valid_months:
            raise serializers.ValidationError("Invalid month. Must be a full month name.")
        return value
    
    def validate_year(self, value):
        """
        Validate year.
        """
        if value < 2020 or value > 2030:
            raise serializers.ValidationError("Year must be between 2020 and 2030.")
        return value
