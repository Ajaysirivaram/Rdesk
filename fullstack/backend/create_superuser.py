#!/usr/bin/env python
"""
Script to create a Django superuser
Run this with: python create_superuser.py
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'camelq_payslip.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.management import execute_from_command_line

def create_superuser():
    """Create a superuser for Django admin"""
    User = get_user_model()
    
    # Check if superuser already exists
    if User.objects.filter(is_superuser=True).exists():
        print("Superuser already exists!")
        return
    
    # Create superuser
    username = 'admin'
    email = 'admin@example.com'
    password = 'admin123'  # Change this to a secure password
    
    try:
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        print(f"Superuser created successfully!")
        print(f"Username: {username}")
        print(f"Email: {email}")
        print(f"Password: {password}")
        print(f"Admin URL: https://your-backend-url.up.railway.app/admin/")
    except Exception as e:
        print(f"Error creating superuser: {e}")

if __name__ == "__main__":
    create_superuser()
