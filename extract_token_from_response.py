#!/usr/bin/env python3
"""
Extract Token from the Response Data Visible in Screenshot
"""

import json
from datetime import datetime, timedelta

def extract_from_screenshot_data():
    """Extract and update tokens from the response data I can see"""
    
    print("🔍 Looking at your screenshot data...")
    
    # From the screenshot, I can see this data structure:
    # success: true
    # message: "User token is valid"
    # data: {
    #   employee: {
    #     id: "28c5e780-3707-11ec-bb31-dde416ab9f61",
    #     firstName: "Dayne",
    #     lastName: "Levinrad", 
    #     email: "dayne@getbird.co.za",
    #     refreshToken: "qRRSyxhfd8TmSaWxH1MOwaow1LogckUq",
    #     organisationId: "1476d7a5-b7b2-4b18-85c6-33730cf37a12",
    #     organisationAdmin: true,
    #     ...
    #   }
    # }
    
    # I can see there's more data in the response that's partially cut off
    # Let me create what I can extract and ask for the missing bearer token
    
    known_data = {
        "refresh_token": "qRRSyxhfd8TmSaWxH1MOwaow1LogckUq",
        "employee_id": "28c5e780-3707-11ec-bb31-dde416ab9f61",
        "organisation_id": "1476d7a5-b7b2-4b18-85c6-33730cf37a12"
    }
    
    print("✅ Extracted data from screenshot:")
    print(f"   Employee ID: {known_data['employee_id']}")
    print(f"   Organisation ID: {known_data['organisation_id']}")
    print(f"   Refresh Token: {known_data['refresh_token']}")
    
    print("\n🔍 From your browser Network tab, in the Response for:")
    print("   POST https://api.munch.cloud/api/auth-internal/token")
    print("\nLook for one of these fields in the JSON response:")
    print("   - data.token")
    print("   - data.accessToken") 
    print("   - data.bearerToken")
    print("   - token")
    print("   - accessToken")
    
    print("\nThe token should be a long string starting with 'eyJ'")
    print("Example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    
    # Try to help find it in the response
    print("\n💡 Quick way to find it:")
    print("   1. In Network tab, click on the auth-internal/token request")
    print("   2. Click 'Response' tab")  
    print("   3. Search for 'eyJ' - this will highlight the bearer token")
    print("   4. Copy the full token string")
    
    bearer_token = input("\nPaste the bearer token (starting with eyJ): ").strip()
    
    if bearer_token and bearer_token.startswith('eyJ'):
        # Create complete token structure
        complete_tokens = {
            "bearer_token": bearer_token,
            "refresh_token": known_data["refresh_token"],
            "employee_id": known_data["employee_id"],
            "organisation_id": known_data["organisation_id"],
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()  # Estimate 24h
        }
        
        # Save to file
        with open('munch_tokens.json', 'w') as f:
            json.dump(complete_tokens, f, indent=2)
        
        print("\n✅ Complete tokens saved!")
        print("🎉 Integration is ready to run!")
        
        # Test the integration
        print("\n🚀 Next steps:")
        print("1. Start the integration: ./start_integration.sh")
        print("2. Test with Amanda Gifford (PID: B4FTo4XzpWEwIj)")
        print("   She has 1 free coffee waiting!")
        
        return True
    else:
        print("❌ No valid bearer token provided")
        return False

if __name__ == "__main__":
    extract_from_screenshot_data() 