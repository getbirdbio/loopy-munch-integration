#!/usr/bin/env python3
"""
Extract Fresh Tokens from Successful Munch Login
Based on the successful login you just performed
"""

import requests
import json
import jwt
from datetime import datetime, timedelta
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_fresh_tokens_from_internal_auth():
    """Get fresh tokens using the internal auth endpoint that worked"""
    
    base_url = "https://api.munch.cloud"
    
    # Your credentials that just worked
    email = "dayne@getbird.co.za"
    password = "LevinradD@yne870326"
    
    print(f"🔑 Getting fresh tokens from internal auth endpoint...")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    # Use the internal auth endpoint that worked in your browser
    auth_url = f"{base_url}/api/auth-internal/token"
    
    try:
        response = requests.post(
            auth_url,
            json=login_data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "MunchPOS-Integration/1.0"
            },
            timeout=30,
            verify=False
        )
        
        print(f"Auth response: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Login successful!")
            
            if result.get('success'):
                data = result.get('data', {})
                employee_data = data.get('employee', {})
                
                # Extract token information
                bearer_token = data.get('token') or data.get('accessToken')
                refresh_token = employee_data.get('refreshToken')
                employee_id = employee_data.get('id')
                organisation_id = employee_data.get('organisationId')
                
                if bearer_token and refresh_token:
                    # Decode JWT to get expiry
                    try:
                        decoded = jwt.decode(bearer_token, options={"verify_signature": False})
                        exp_timestamp = decoded.get('exp')
                        expires_at = datetime.fromtimestamp(exp_timestamp) if exp_timestamp else None
                    except:
                        expires_at = datetime.now() + timedelta(hours=24)  # Default 24h
                    
                    # Update tokens file
                    new_tokens = {
                        "bearer_token": bearer_token,
                        "refresh_token": refresh_token,
                        "employee_id": employee_id,
                        "organisation_id": organisation_id,
                        "expires_at": expires_at.isoformat() if expires_at else None
                    }
                    
                    with open('munch_tokens.json', 'w') as f:
                        json.dump(new_tokens, f, indent=2)
                    
                    print("✅ Fresh tokens saved successfully!")
                    print(f"   Employee ID: {employee_id}")
                    print(f"   Organisation ID: {organisation_id}")
                    print(f"   Refresh Token: {refresh_token}")
                    print(f"   Expires: {expires_at}")
                    
                    # Test the new token immediately
                    test_new_token(bearer_token)
                    
                    return True
                else:
                    print("❌ Missing token data in response")
                    print(f"Full response: {result}")
                    return False
            else:
                print("❌ Login response indicates failure")
                print(f"Response: {result}")
                return False
        else:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return False

def test_new_token(bearer_token):
    """Test the new token with a simple API call"""
    print(f"\n🧪 Testing new token...")
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': bearer_token,
        'User-Agent': 'MunchPOS-Integration/1.0'
    }
    
    # Test with a simple endpoint
    test_url = "https://api.munch.cloud/api/employees/me"
    
    try:
        response = requests.get(test_url, headers=headers, timeout=10, verify=False)
        print(f"Token test: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ New token is working!")
        else:
            print(f"⚠️ Token test returned: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ Token test error: {e}")

def create_updated_tokens_from_screenshot():
    """Create tokens file based on the data from your successful login screenshot"""
    print(f"📸 Creating tokens from your successful login data...")
    
    # Data extracted from your screenshots
    new_tokens = {
        "bearer_token": "",  # We'll get this from a fresh login
        "refresh_token": "qRRSyxhfd8TmSaWxH1MOwaow1LogckUq",  # From your screenshot
        "employee_id": "28c5e780-3707-11ec-bb31-dde416ab9f61",
        "organisation_id": "1476d7a5-b7b2-4b18-85c6-33730cf37a12",
        "expires_at": None  # Will be set when we get bearer token
    }
    
    print(f"🔄 Now getting fresh bearer token...")
    return get_fresh_tokens_from_internal_auth()

if __name__ == "__main__":
    success = create_updated_tokens_from_screenshot()
    if success:
        print("\n🎉 SUCCESS! Fresh tokens ready!")
        print("🚀 You can now restart the integration service:")
        print("   ./start_integration.sh")
        print("\n☕ Ready to test with Amanda Gifford (PID: B4FTo4XzpWEwIj)")
        print("   She has 1 free coffee waiting (R40 credit)!")
    else:
        print("\n❌ Failed to get fresh tokens. Please try the manual approach again.") 