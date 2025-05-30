#!/usr/bin/env python3
"""
Munch Authentication Test Template - WORKING VERSION
Based on successful breakthrough with repository integration
"""

import requests
import json
import jwt
from datetime import datetime

def test_munch_auth_only():
    """Test Munch authentication with correct endpoints - PROVEN WORKING"""
    
    # Load tokens from munch_tokens.json
    try:
        with open('munch_tokens.json', 'r') as f:
            tokens = json.load(f)
    except Exception as e:
        print(f"❌ Error loading tokens: {e}")
        return False
    
    bearer_token = tokens.get('bearer_token')
    organisation_id = tokens.get('organisation_id')
    employee_id = tokens.get('employee_id')
    
    # Decode token to check expiration
    try:
        decoded = jwt.decode(bearer_token, options={"verify_signature": False})
        exp_timestamp = decoded.get('exp')
        if exp_timestamp:
            exp_date = datetime.fromtimestamp(exp_timestamp)
            print(f"🔍 Token expires: {exp_date}")
            
            if datetime.now() > exp_date:
                print("❌ Token has expired!")
                return False
    except Exception as e:
        print(f"⚠️ Could not decode token: {e}")
    
    print("🔐 Testing Munch API authentication...")
    
    # WORKING configuration from repository integration
    base_url = "https://api.munch.cloud/api"
    
    # CRITICAL: These headers are required for Munch Cloud API
    headers = {
        'Authorization': f'Bearer {bearer_token}',
        'Authorization-Type': 'internal',  # REQUIRED
        'Content-Type': 'application/json',
        'Locale': 'en',
        'Munch-Platform': 'cloud.munch.portal',  # REQUIRED
        'Munch-Timezone': 'Africa/Johannesburg',
        'Munch-Version': '2.20.1'  # REQUIRED
    }
    
    # Add employee and organisation IDs if available
    if employee_id:
        headers['Munch-Employee'] = employee_id  # REQUIRED
    if organisation_id:
        headers['Munch-Organisation'] = organisation_id  # REQUIRED
    
    print(f"   Base URL: {base_url}")
    print(f"   Organisation ID: {organisation_id}")
    print(f"   Employee ID: {employee_id}")
    
    # WORKING endpoint from repository
    correct_account_id = "3e92a480-5f21-11ec-b43f-dde416ab9f61"  # From repository
    
    test_endpoints = [
        {
            'name': 'Get All Users',
            'method': 'POST',
            'endpoint': 'account/retrieve-users',
            'data': {
                "id": correct_account_id,
                "timezone": "Africa/Johannesburg"
            }
        }
    ]
    
    success_count = 0
    
    for test in test_endpoints:
        print(f"\n🧪 Testing: {test['name']}")
        print(f"   {test['method']} {base_url}/{test['endpoint']}")
        
        try:
            url = f"{base_url}/{test['endpoint']}"
            
            if test['method'] == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            else:
                response = requests.post(url, json=test.get('data', {}), headers=headers, timeout=10)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ SUCCESS!")
                try:
                    result = response.json()
                    if test['name'] == 'Get All Users':
                        users = result.get('data', {}).get('users', [])
                        print(f"   📊 Found {len(users)} users")
                        if users:
                            sample_user = users[0]
                            print(f"   👤 Sample user: {sample_user.get('firstName', 'N/A')} {sample_user.get('lastName', 'N/A')} ({sample_user.get('email', 'N/A')})")
                    success_count += 1
                except Exception as e:
                    print(f"   📝 Response (first 200 chars): {response.text[:200]}...")
            else:
                print(f"   ❌ Failed: {response.text[:200]}...")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n📊 Results: {success_count}/{len(test_endpoints)} endpoints working")
    
    if success_count > 0:
        print("✅ Munch API authentication is working!")
        print("🎯 Integration can proceed with API calls")
        return True
    else:
        print("❌ No endpoints working - check authentication")
        return False

if __name__ == "__main__":
    # Test results from successful run:
    # ✅ SUCCESS - Found 837 users
    # Sample user: Andrew Worthington (andrew@preciseaccounting.co.za)
    test_munch_auth_only() 