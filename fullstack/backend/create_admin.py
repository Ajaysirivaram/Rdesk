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
    
    try:
        # Delete existing admin if exists
        User.objects.filter(username=username).delete()
        
        # Create new admin user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=True,
            is_superuser=True
        )
        
        print(f"✅ Admin user created successfully!")
        print(f"Username: {username}")
        print(f"Password: {password}")
        print(f"Email: {email}")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")

if __name__ == "__main__":
    create_admin()
