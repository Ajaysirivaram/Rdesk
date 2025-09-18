from django.core.management.base import BaseCommand
from departments.models import Department

class Command(BaseCommand):
    help = 'Create sample departments for the application'

    def handle(self, *args, **options):
        departments_data = [
            {'department_code': 'IT', 'department_name': 'Information Technology', 'description': 'Software development and IT support'},
            {'department_code': 'HR', 'department_name': 'Human Resources', 'description': 'Human resources and employee management'},
            {'department_code': 'FIN', 'department_name': 'Finance', 'description': 'Financial management and accounting'},
            {'department_code': 'MKT', 'department_name': 'Marketing', 'description': 'Marketing and business development'},
            {'department_code': 'OPS', 'department_name': 'Operations', 'description': 'Operations and project management'},
            {'department_code': 'SALES', 'department_name': 'Sales', 'description': 'Sales and customer relations'},
        ]
        
        created_count = 0
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
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created department: {department.department_name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ Department already exists: {department.department_name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'🎉 Created {created_count} new departments!')
        )
