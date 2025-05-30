#!/usr/bin/env python3
"""
Alternative Munch Token Refresh Approaches
"""

import requests
import json
import jwt
from datetime import datetime, timedelta
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def try_alternative_refresh():
    """Try alternative methods to refresh the Munch token"""
    
    # Load current tokens
    try:
        with open('munch_tokens.json', 'r') as f:
            tokens = json.load(f)
    except Exception as e:
        print(f"❌ Error loading tokens: {e}")
        return False
    
    refresh_token = tokens.get('refresh_token')
    bearer_token = tokens.get('bearer_token')
    organisation_id = tokens.get('organisation_id')
    employee_id = tokens.get('employee_id')
    
    print("🔄 Trying alternative token refresh methods...")
    print(f"Employee ID: {employee_id}")
    print(f"Organisation ID: {organisation_id}")
    print(f"Refresh Token: {refresh_token}")
    
    base_url = "https://api.munch.cloud"
    
    # Method 1: Standard refresh endpoint with different headers
    print("\n🧪 Method 1: Standard refresh with Authorization header")
    try:
        refresh_url = f"{base_url}/api/auth/refresh"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {bearer_token}',
            'User-Agent': 'MunchPOS-Integration/1.0'
        }
        data = {'refreshToken': refresh_token}
        
        response = requests.post(refresh_url, json=data, headers=headers, timeout=10, verify=False)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            handle_successful_refresh(response.json())
            return True
            
    except Exception as e:
        print(f"   Error: {e}")
    
    # Method 2: Try refresh without bearer token
    print("\n🧪 Method 2: Refresh without authorization header")
    try:
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'MunchPOS-Integration/1.0'
        }
        data = {'refreshToken': refresh_token}
        
        response = requests.post(refresh_url, json=data, headers=headers, timeout=10, verify=False)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            handle_successful_refresh(response.json())
            return True
            
    except Exception as e:
        print(f"   Error: {e}")
    
    # Method 3: Try token endpoint
    print("\n🧪 Method 3: Token endpoint")
    try:
        token_url = f"{base_url}/api/auth/token"
        data = {
            'refreshToken': refresh_token,
            'grant_type': 'refresh_token'
        }
        
        response = requests.post(token_url, json=data, headers=headers, timeout=10, verify=False)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            handle_successful_refresh(response.json())
            return True
            
    except Exception as e:
        print(f"   Error: {e}")
    
    # Method 4: Try renew endpoint
    print("\n🧪 Method 4: Renew endpoint")
    try:
        renew_url = f"{base_url}/api/auth/renew"
        data = {'token': refresh_token}
        
        response = requests.post(renew_url, json=data, headers=headers, timeout=10, verify=False)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            handle_successful_refresh(response.json())
            return True
            
    except Exception as e:
        print(f"   Error: {e}")
    
    # Method 5: Try user-specific refresh
    print("\n🧪 Method 5: User-specific refresh")
    try:
        user_refresh_url = f"{base_url}/api/users/{employee_id}/refresh"
        data = {'refreshToken': refresh_token}
        
        response = requests.post(user_refresh_url, json=data, headers=headers, timeout=10, verify=False)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            handle_successful_refresh(response.json())
            return True
            
    except Exception as e:
        print(f"   Error: {e}")
    
    # Method 6: Try organization-specific refresh
    print("\n🧪 Method 6: Organization-specific refresh")
    try:
        org_refresh_url = f"{base_url}/api/organisations/{organisation_id}/auth/refresh"
        data = {'refreshToken': refresh_token}
        
        response = requests.post(org_refresh_url, json=data, headers=headers, timeout=10, verify=False)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            handle_successful_refresh(response.json())
            return True
            
    except Exception as e:
        print(f"   Error: {e}")
    
    # Method 7: Try with Payment Gateway credentials as headers
    print("\n🧪 Method 7: Using payment gateway as API credentials")
    try:
        headers_with_gateway = {
            'Content-Type': 'application/json',
            'X-API-Key': '4657c04b355040a497baf6046bd304da',
            'X-Access-Key': 'ZGXGX5PJQPV6VZ6R4YCW',
            'X-Secret-Key': 'JnyYHxbU7JKAe63C*tCdhUh1J9KXMpV8s9nM3UFu',
            'User-Agent': 'MunchPOS-PaymentGateway/1.0'
        }
        data = {'refreshToken': refresh_token}
        
        response = requests.post(refresh_url, json=data, headers=headers_with_gateway, timeout=10, verify=False)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            handle_successful_refresh(response.json())
            return True
            
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n❌ All refresh methods failed. May need manual login.")
    return False

def handle_successful_refresh(response_data):
    """Handle successful token refresh"""
    print(f"\n✅ Token refresh successful!")
    
    # Extract new token
    new_token = response_data.get('token') or response_data.get('accessToken') or response_data.get('access_token')
    new_refresh = response_data.get('refreshToken') or response_data.get('refresh_token')
    
    if new_token:
        # Decode to get expiry
        try:
            decoded = jwt.decode(new_token, options={"verify_signature": False})
            exp_timestamp = decoded.get('exp')
            expires_at = datetime.fromtimestamp(exp_timestamp) if exp_timestamp else None
        except:
            expires_at = datetime.now() + timedelta(hours=24)
        
        # Update tokens file
        try:
            with open('munch_tokens.json', 'r') as f:
                current_tokens = json.load(f)
            
            current_tokens.update({
                "bearer_token": new_token,
                "refresh_token": new_refresh or current_tokens.get('refresh_token'),
                "expires_at": expires_at.isoformat() if expires_at else None
            })
            
            with open('munch_tokens.json', 'w') as f:
                json.dump(current_tokens, f, indent=2)
            
            print(f"📅 New expiry: {expires_at}")
            print(f"💾 Tokens saved to munch_tokens.json")
            return True
            
        except Exception as e:
            print(f"❌ Error saving tokens: {e}")
            return False
    else:
        print(f"❌ No new token in response: {response_data}")
        return False

if __name__ == "__main__":
    try_alternative_refresh() 