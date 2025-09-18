#!/usr/bin/env python3
"""
Script to create departments via API
"""
import requests
import json

def create_departments():
    base_url = "https://web-production-5f64c.up.railway.app"
    api_url = f"{base_url}/api/departments/create-sample/"
    
    print(f"Creating departments via API: {api_url}")
    
    try:
        response = requests.post(api_url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print(f"Response Data: {json.dumps(data, indent=2)}")
            
            if data.get('success'):
                print(f"✅ Successfully created {data.get('message', 'departments')}")
                print(f"📊 Total departments now: {data.get('total_departments', 0)}")
                
                # List created departments
                created_depts = data.get('created_departments', [])
                if created_depts:
                    print("\nCreated departments:")
                    for dept in created_depts:
                        print(f"  - {dept.get('name')} ({dept.get('code')})")
            else:
                print(f"❌ Error: {data.get('error', 'Unknown error')}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"💥 Error calling API: {e}")

if __name__ == "__main__":
    create_departments()
