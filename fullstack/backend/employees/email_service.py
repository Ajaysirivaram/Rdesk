from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import logging

class EmployeeEmailService:
    """
    Service for sending employee-related emails.
    """
    
    def __init__(self):
        self.from_email = settings.DEFAULT_FROM_EMAIL
        self.company_name = "CamelQ Software Solutions Pvt. Ltd."
        self.company_address = "13th FLOOR, MANJEERA TRINITY CORPORATE, JNTU - HITECH CITY ROAD, 3/d PHASE, KPHB, KUKATPALLY, HYDERABAD - 500072"
        self.login_url = "https://webmail.camelq.co.in"
    
    def send_welcome_email(self, employee):
        """
        Send welcome email to new employee with admin-provided password.
        
        Args:
            employee: Employee instance with personal_email and password
            
        Returns:
            tuple: (success: bool, message: str)
        """
        if not employee.personal_email:
            return False, "No personal email address provided"
        
        if not employee.password:
            return False, "No password provided"
        
        try:
            # Prepare email context
            context = {
                'employee_name': employee.name,
                'email': employee.email,  # System login email
                'personal_email': employee.personal_email,  # Email where this is sent
                'password': employee.password,
                'company_name': self.company_name,
                'company_address': self.company_address,
                'login_url': self.login_url
            }
            
            # Render email templates
            html_content = render_to_string('emails/welcome_email.html', context)
            text_content = render_to_string('emails/welcome_email.txt', context)
            
            # Create email
            subject = f"Welcome to {self.company_name}"
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=self.from_email,
                to=[employee.personal_email]  # Send to personal email
            )
            email.attach_alternative(html_content, "text/html")
            
            # Send email
            email.send()
            
            logging.getLogger('employees').info(
                f"Welcome email sent successfully to {employee.personal_email} for employee {employee.employee_id}"
            )
            return True, "Welcome email sent successfully"
            
        except Exception as e:
            error_msg = f"Failed to send welcome email to {employee.personal_email}: {str(e)}"
            logging.getLogger('employees').error(error_msg)
            return False, error_msg
    
    def send_bulk_welcome_emails(self, employees):
        """
        Send welcome emails to multiple employees.
        
        Args:
            employees: List of Employee instances
            
        Returns:
            dict: Results with success/failure counts and details
        """
        results = {
            'total': len(employees),
            'sent': 0,
            'failed': 0,
            'details': []
        }
        
        for employee in employees:
            success, message = self.send_welcome_email(employee)
            
            result_detail = {
                'employee_id': employee.employee_id,
                'employee_name': employee.name,
                'email': employee.email,
                'success': success,
                'message': message
            }
            
            results['details'].append(result_detail)
            
            if success:
                results['sent'] += 1
            else:
                results['failed'] += 1
        
        return results
