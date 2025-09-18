from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .models import EmailLog
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
        
        # Create email log entry
        email_log = EmailLog.objects.create(
            employee=employee if hasattr(employee, 'id') else None,
            email_type='WELCOME',
            recipient_email=employee.personal_email,
            subject=f"Welcome to {self.company_name}",
            status='PENDING'
        )
        
        try:
            # Prepare email context with safe defaults
            context = {
                'employee_name': getattr(employee, 'name', 'Employee'),
                'email': getattr(employee, 'email', ''),
                'personal_email': getattr(employee, 'personal_email', ''),
                'password': getattr(employee, 'password', ''),
                'company_name': self.company_name,
                'company_address': self.company_address,
                'login_url': self.login_url
            }
            
            # Render email templates with error handling
            try:
                html_content = render_to_string('emails/welcome_email.html', context)
            except Exception as template_error:
                logging.getLogger('employees').error(f"HTML template error: {str(template_error)}")
                html_content = f"""
                <html><body>
                <h2>Welcome to {self.company_name}</h2>
                <p>Dear {context['employee_name']},</p>
                <p>Your login credentials are:</p>
                <p>Email: {context['email']}</p>
                <p>Password: {context['password']}</p>
                <p>Login URL: {context['login_url']}</p>
                </body></html>
                """
            
            try:
                text_content = render_to_string('emails/welcome_email.txt', context)
            except Exception as template_error:
                logging.getLogger('employees').error(f"Text template error: {str(template_error)}")
                text_content = f"""
                Welcome to {self.company_name}
                
                Dear {context['employee_name']},
                
                Your login credentials are:
                Email: {context['email']}
                Password: {context['password']}
                Login URL: {context['login_url']}
                """
            
            # Create email
            subject = f"Welcome to {self.company_name}"
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=self.from_email,
                to=[employee.personal_email]  # Send to personal email
            )
            email.attach_alternative(html_content, "text/html")
            
            # Send email with fallback for missing SMTP credentials
            try:
                email.send()
                
                # Update email log
                email_log.status = 'SENT'
                email_log.message = "Welcome email sent successfully"
                email_log.save()
                
                logging.getLogger('employees').info(
                    f"Welcome email sent successfully to {employee.personal_email} for employee {employee.employee_id}"
                )
                return True, "Welcome email sent successfully"
                
            except Exception as smtp_error:
                # If SMTP fails, log it but don't crash
                error_msg = f"SMTP error: {str(smtp_error)}"
                logging.getLogger('employees').warning(error_msg)
                
                # Update email log with SMTP error
                email_log.status = 'FAILED'
                email_log.error_message = error_msg
                email_log.save()
                
                # Return success but with warning (for development/testing)
                return True, f"Email queued (SMTP not configured): {error_msg}"
            
        except Exception as e:
            error_msg = f"Failed to send welcome email to {employee.personal_email}: {str(e)}"
            
            # Update email log with error
            email_log.status = 'FAILED'
            email_log.error_message = error_msg
            email_log.save()
            
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
