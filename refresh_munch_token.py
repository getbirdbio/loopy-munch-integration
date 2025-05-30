#!/usr/bin/env python3
"""
Refresh Munch POS Authentication Token
"""

import requests
import json
from datetime import datetime

def refresh_munch_token():
    """Refresh the Munch authentication token using refresh token"""
    
    # Load current tokens
    try:
        with open('munch_tokens.json', 'r') as f:
            tokens = json.load(f)
    except Exception as e:
        print(f"❌ Error loading tokens: {e}")
        return False
    
    refresh_token = tokens.get('refresh_token')
    organisation_id = tokens.get('organisation_id')
    
    if not refresh_token:
        print("❌ No refresh token found")
        return False
    
    print("🔄 Refreshing Munch authentication token...")
    
    # Refresh token endpoint
    refresh_url = "https://api.munch.cloud/api/auth/refresh"
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'{tokens["bearer_token"]}'  # Sometimes needed for refresh
    }
    
    refresh_data = {
        'refreshToken': refresh_token
    }
    
    try:
        response = requests.post(refresh_url, json=refresh_data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            new_tokens = response.json()
            
            # Update tokens file
            updated_tokens = {
                "bearer_token": new_tokens.get('accessToken', new_tokens.get('token')),
                "refresh_token": new_tokens.get('refreshToken', refresh_token),
                "employee_id": tokens.get('employee_id'),
                "organisation_id": organisation_id,
                "expires_at": new_tokens.get('expiresAt', 'unknown')
            }
            
            # Save updated tokens
            with open('munch_tokens.json', 'w') as f:
                json.dump(updated_tokens, f, indent=2)
            
            print("✅ Token refreshed successfully!")
            print(f"📅 New expiry: {updated_tokens['expires_at']}")
            return True
            
        else:
            print(f"❌ Token refresh failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error refreshing token: {e}")
        return False

if __name__ == "__main__":
    refresh_munch_token() 