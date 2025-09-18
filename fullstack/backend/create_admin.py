#!/usr/bin/env python
"""
Simple script to create admin user for login
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'camelq_payslip.settings')
django.setup()

from django.contrib.auth import get_user_model

def create_admin():
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
        
        print(f"✅ Admin user created successfully!")
        print(f"Username: {username}")
        print(f"Password: {password}")
        print(f"Email: {email}")
        print(f"Full Name: {full_name}")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_admin()
