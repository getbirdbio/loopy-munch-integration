#!/usr/bin/env python3
"""
Update Munch Tokens from Successful Screenshot Data
Manually input the token from your successful browser login
"""

import json
import jwt
from datetime import datetime, timedelta

def update_tokens_from_screenshot():
    """Update tokens using the data from your successful login"""
    
    print("🔑 Updating tokens from your successful browser login...")
    
    # I can see from your screenshot that you got a successful response
    # The refreshToken is visible: "qRRSyxhfd8TmSaWxH1MOwaow1LogckUq"
    # But I need the bearer token (accessToken) from the response
    
    print("\nFrom your screenshot, I can see:")
    print("✅ Successful login to: https://api.munch.cloud/api/auth-internal/token")
    print("✅ Response shows: success: true, message: 'User token is valid'")
    print("✅ Refresh Token: qRRSyxhfd8TmSaWxH1MOwaow1LogckUq")
    
    # Known data from the screenshot
    refresh_token = "qRRSyxhfd8TmSaWxH1MOwaow1LogckUq"
    employee_id = "28c5e780-3707-11ec-bb31-dde416ab9f61"
    organisation_id = "1476d7a5-b7b2-4b18-85c6-33730cf37a12"
    
    # Request the bearer token from the user
    print("\n🔍 I need the bearer/access token from your successful login response.")
    print("In your browser's Network tab, look for the response to:")
    print("   POST https://api.munch.cloud/api/auth-internal/token")
    print("\nIn the Response JSON, find the 'token' or 'accessToken' field.")
    print("It should be a long JWT string starting with 'eyJ'")
    
    bearer_token = input("\nPlease paste the bearer token here: ").strip()
    
    if not bearer_token or not bearer_token.startswith('eyJ'):
        print("❌ Invalid token format. Bearer tokens should start with 'eyJ'")
        return False
    
    try:
        # Decode JWT to get expiry
        decoded = jwt.decode(bearer_token, options={"verify_signature": False})
        exp_timestamp = decoded.get('exp')
        expires_at = datetime.fromtimestamp(exp_timestamp) if exp_timestamp else None
        
        print(f"\n📅 Token expires: {expires_at}")
        
        # Create new tokens file
        new_tokens = {
            "bearer_token": bearer_token,
            "refresh_token": refresh_token,
            "employee_id": employee_id,
            "organisation_id": organisation_id,
            "expires_at": expires_at.isoformat() if expires_at else None
        }
        
        # Save tokens
        with open('munch_tokens.json', 'w') as f:
            json.dump(new_tokens, f, indent=2)
        
        print("✅ Tokens updated successfully!")
        print(f"   Employee ID: {employee_id}")
        print(f"   Organisation ID: {organisation_id}")
        print(f"   Refresh Token: {refresh_token[:20]}...")
        print(f"   Bearer Token: {bearer_token[:50]}...")
        print(f"   Expires: {expires_at}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing token: {e}")
        return False

def create_tokens_with_sample():
    """Create a token template if user doesn't have the bearer token handy"""
    
    print("\n🔧 Alternative: Create working tokens with sample data")
    print("I'll create a basic structure and you can update the bearer token later.")
    
    # Use the refresh token from screenshot and known IDs
    sample_tokens = {
        "bearer_token": "PASTE_BEARER_TOKEN_HERE",
        "refresh_token": "qRRSyxhfd8TmSaWxH1MOwaow1LogckUq",
        "employee_id": "28c5e780-3707-11ec-bb31-dde416ab9f61", 
        "organisation_id": "1476d7a5-b7b2-4b18-85c6-33730cf37a12",
        "expires_at": "2025-05-31T12:00:00.000000"
    }
    
    with open('munch_tokens.json', 'w') as f:
        json.dump(sample_tokens, f, indent=2)
    
    print("✅ Template tokens file created!")
    print("📝 To complete setup:")
    print("   1. Open munch_tokens.json")
    print("   2. Replace 'PASTE_BEARER_TOKEN_HERE' with the actual bearer token")
    print("   3. Save the file")
    print("   4. Restart the integration service")
    
    return True

if __name__ == "__main__":
    print("🎯 Choose an option:")
    print("1. Enter bearer token from browser response (recommended)")
    print("2. Create template file to edit manually")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        success = update_tokens_from_screenshot()
    elif choice == "2":
        success = create_tokens_with_sample()
    else:
        print("❌ Invalid choice")
        success = False
    
    if success and choice == "1":
        print("\n🎉 SUCCESS! Integration is ready!")
        print("🚀 Start the integration service:")
        print("   ./start_integration.sh")
        print("\n☕ Test with Amanda Gifford:")
        print("   PID: B4FTo4XzpWEwIj")
        print("   Available: 1 free coffee (R40 credit)")
    elif success:
        print("\n⚠️ Manual step required to complete setup") 