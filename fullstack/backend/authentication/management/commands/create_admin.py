from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Create admin user for the application'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Create or update admin user
        username = 'admin'
        password = 'admin123'
        email = 'admin@example.com'
        full_name = 'Admin User'
        
        try:
            # Delete existing admin if exists
            User.objects.filter(username=username).delete()
            
            # Create new admin user with all required fields
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                full_name=full_name,
                is_staff=True,
                is_superuser=True,
                is_active=True
            )
            
            self.stdout.write(
                self.style.SUCCESS('✅ Admin user created successfully!')
            )
            self.stdout.write(f'Username: {username}')
            self.stdout.write(f'Password: {password}')
            self.stdout.write(f'Email: {email}')
            self.stdout.write(f'Full Name: {full_name}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creating admin user: {e}')
            )
            import traceback
            traceback.print_exc()