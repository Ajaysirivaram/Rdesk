from django.db import models
from django.core.validators import RegexValidator
from departments.models import Department


class Employee(models.Model):
    """
    Employee model for storing employee information.
    """
    PAY_MODE_CHOICES = [
        ('Bank Transfer', 'Bank Transfer'),
        ('NEFT', 'NEFT'),
        ('Cheque', 'Cheque'),
        ('Cash', 'Cash'),
    ]

    # Basic Information
    employee_id = models.CharField(
        max_length=20, 
        unique=True,
        validators=[RegexValidator(
            regex=r'^[A-Z0-9]+$',
            message='Employee ID must contain only uppercase letters and numbers.'
        )]
    )
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    department = models.ForeignKey(
        Department, 
        on_delete=models.CASCADE,
        related_name='employees'
    )
    
    # Personal Information
    dob = models.DateField(verbose_name='Date of Birth')
    doj = models.DateField(verbose_name='Date of Joining')
    
    # Financial Information
    pan = models.CharField(
        max_length=10,
        validators=[RegexValidator(
            regex=r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$',
            message='PAN must be in format: ABCDE1234F'
        )]
    )
    pf_number = models.CharField(max_length=30, verbose_name='PF Number', blank=True, null=True)
    bank_account = models.CharField(max_length=30, verbose_name='Bank Account Number')
    bank_ifsc = models.CharField(
        max_length=15,
        validators=[RegexValidator(
            regex=r'^[A-Z]{4}0[A-Z0-9]{6}$',
            message='IFSC must be in format: ABCD0123456'
        )]
    )
    pay_mode = models.CharField(max_length=20, choices=PAY_MODE_CHOICES, default='NEFT')
    
    # Additional Information
    location = models.CharField(max_length=100)
    health_card_no = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True, help_text='Employee email for system login')
    personal_email = models.EmailField(max_length=255, blank=True, null=True, help_text='Personal email for welcome emails and communication')
    
    # Login Credentials
    password = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text="Temporary password for system access"
    )
    password_changed = models.BooleanField(
        default=False,
        help_text="Whether employee has changed their initial password"
    )
    password_set_date = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True,
        help_text="When the password was set"
    )
    
    # Salary Information
    lpa = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        verbose_name='LPA (Lakhs Per Annum)',
        help_text='Annual salary in lakhs (e.g., 4.5 for 4.5 LPA)',
        null=True,
        blank=True
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'employees'
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.employee_id})"

    @property
    def full_name(self):
        return self.name

    @property
    def department_name(self):
        return self.department.department_name


class SalaryStructure(models.Model):
    """
    Salary structure model for storing employee salary information.
    """
    SALARY_TYPE_CHOICES = [
        ('SALARY', 'Salary'),
        ('STIPEND', 'Stipend'),
    ]

    employee = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE,
        related_name='salary_structures'
    )
    salary_type = models.CharField(max_length=20, choices=SALARY_TYPE_CHOICES)
    annual_ctc = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Annual CTC')
    effective_from = models.DateField(default=models.functions.Now)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'salary_structures'
        verbose_name = 'Salary Structure'
        verbose_name_plural = 'Salary Structures'
        ordering = ['-effective_from']

    def __str__(self):
        return f"{self.employee.name} - {self.salary_type} ({self.annual_ctc})"

    @property
    def monthly_salary(self):
        return self.annual_ctc / 12

    @property
    def basic_salary(self):
        return self.monthly_salary * 0.4

    @property
    def hra(self):
        return self.basic_salary * 0.2

    @property
    def da(self):
        return self.basic_salary * 0.1

    @property
    def conveyance(self):
        return 1600  # Fixed amount

    @property
    def medical(self):
        return 1250  # Fixed amount

    @property
    def pf_employee(self):
        return self.basic_salary * 0.12

    @property
    def pf_employer(self):
        return self.basic_salary * 0.12

    @property
    def professional_tax(self):
        return 200  # Fixed amount

    @property
    def special_allowance(self):
        return self.monthly_salary - (
            self.basic_salary + self.da + self.hra + 
            self.medical + self.conveyance + self.pf_employer
        )


class MonthlySalaryData(models.Model):
    """
    Model for storing monthly salary data uploaded via Excel.
    """
    employee = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE,
        related_name='monthly_salaries'
    )
    month = models.CharField(max_length=20)
    year = models.IntegerField()
    
    # Salary Components
    basic = models.DecimalField(max_digits=10, decimal_places=2)
    hra = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='House Rent Allowance')
    da = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Dearness Allowance')
    conveyance = models.DecimalField(max_digits=10, decimal_places=2)
    medical = models.DecimalField(max_digits=10, decimal_places=2)
    special_allowance = models.DecimalField(max_digits=10, decimal_places=2)
    pf_employee = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='PF Employee')
    
    # Deductions
    professional_tax = models.DecimalField(max_digits=10, decimal_places=2)
    pf_employer = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='PF Employer')
    other_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    salary_advance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Work Days Information
    work_days = models.IntegerField()
    days_in_month = models.IntegerField()
    lop_days = models.IntegerField(default=0, verbose_name='Loss of Pay Days')
    
    # Metadata
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        'authentication.AdminUser', 
        on_delete=models.CASCADE,
        related_name='uploaded_salaries'
    )
    
    class Meta:
        db_table = 'monthly_salary_data'
        verbose_name = 'Monthly Salary Data'
        verbose_name_plural = 'Monthly Salary Data'
        ordering = ['-year', '-month']
        unique_together = ['employee', 'month', 'year']

    def __str__(self):
        return f"{self.employee.name} - {self.month} {self.year}"

    @property
    def total_earnings(self):
        return self.basic + self.hra + self.da + self.conveyance + self.medical + self.special_allowance + self.pf_employee

    @property
    def total_deductions(self):
        return self.professional_tax + self.pf_employer + self.other_deductions + self.salary_advance

    @property
    def net_pay(self):
        return self.total_earnings - self.total_deductions


class ActualSalaryCredited(models.Model):
    """
    Model for storing actual salary credited to employees for a month.
    """
    employee = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE,
        related_name='actual_salaries'
    )
    month = models.CharField(max_length=20)
    year = models.IntegerField()
    
    # Actual salary credited
    actual_salary_credited = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Metadata
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        'authentication.AdminUser', 
        on_delete=models.CASCADE,
        related_name='uploaded_actual_salaries'
    )
    
    class Meta:
        db_table = 'actual_salary_credited'
        verbose_name = 'Actual Salary Credited'
        verbose_name_plural = 'Actual Salaries Credited'
        ordering = ['-year', '-month']
        unique_together = ['employee', 'month', 'year']

    def __str__(self):
        return f"{self.employee.name} - {self.month} {self.year} - ₹{self.actual_salary_credited}"


class EmailLog(models.Model):
    """
    Model to track email sending history.
    """
    EMAIL_TYPE_CHOICES = [
        ('WELCOME', 'Welcome Email'),
        ('PAYSLIP', 'Payslip Email'),
        ('BULK_WELCOME', 'Bulk Welcome Email'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
    ]

    employee = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE,
        related_name='email_logs',
        null=True,
        blank=True
    )
    email_type = models.CharField(max_length=20, choices=EMAIL_TYPE_CHOICES)
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    message = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'email_logs'
        verbose_name = 'Email Log'
        verbose_name_plural = 'Email Logs'
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.email_type} to {self.recipient_email} - {self.status}"