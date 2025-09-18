#!/usr/bin/env python3
"""
Script to create departments directly via the main API endpoint
"""
import requests
import json

def create_departments():
    base_url = "https://web-production-5f64c.up.railway.app"
    api_url = f"{base_url}/api/departments/"
    
    departments_data = [
        {'department_code': 'IT', 'department_name': 'Information Technology', 'description': 'Software development and IT support'},
        {'department_code': 'HR', 'department_name': 'Human Resources', 'description': 'Human resources and employee management'},
        {'department_code': 'FIN', 'department_name': 'Finance', 'description': 'Financial management and accounting'},
        {'department_code': 'MKT', 'department_name': 'Marketing', 'description': 'Marketing and business development'},
        {'department_code': 'OPS', 'department_name': 'Operations', 'description': 'Operations and project management'},
        {'department_code': 'SALES', 'department_name': 'Sales', 'description': 'Sales and customer relations'},
    ]
    
    print(f"Creating departments via API: {api_url}")
    
    created_count = 0
    for dept_data in departments_data:
        try:
            print(f"Creating department: {dept_data['department_name']}")
            response = requests.post(api_url, json=dept_data)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 201:
                data = response.json()
                print(f"✅ Created: {data.get('department_name', 'Unknown')}")
                created_count += 1
            else:
                print(f"❌ Error creating {dept_data['department_name']}: {response.text}")
                
        except Exception as e:
            print(f"💥 Error creating {dept_data['department_name']}: {e}")
    
    print(f"\n🎉 Created {created_count} departments successfully!")
    
    # Verify departments were created
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Total departments now: {data.get('count', 0)}")
            if data.get('results'):
                print("Departments:")
                for dept in data['results']:
                    print(f"  - {dept.get('department_name')} ({dept.get('department_code')})")
    except Exception as e:
        print(f"Error verifying departments: {e}")

if __name__ == "__main__":
    create_departments()
