#!/usr/bin/env python
"""
Check if admin user exists
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'camelq_payslip.settings')
django.setup()

from django.contrib.auth import get_user_model

def check_admin():
    User = get_user_model()
    
    try:
        admin_user = User.objects.filter(username='admin').first()
        if admin_user:
            print(f"✅ Admin user exists!")
            print(f"Username: {admin_user.username}")
            print(f"Email: {admin_user.email}")
            print(f"Is Active: {admin_user.is_active}")
            print(f"Is Staff: {admin_user.is_staff}")
            print(f"Is Superuser: {admin_user.is_superuser}")
        else:
            print("❌ Admin user does not exist!")
            
        # Check total users
        total_users = User.objects.count()
        print(f"Total users in database: {total_users}")
        
    except Exception as e:
        print(f"❌ Error checking admin user: {e}")

if __name__ == "__main__":
    check_admin()
