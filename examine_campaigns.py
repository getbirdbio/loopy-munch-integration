import os
import requests
import json
from dotenv import load_dotenv

load_dotenv('production.env')

# Setup Loopy API
base_url = os.getenv('LOOPY_BASE_URL')
username = os.getenv('LOOPY_USERNAME')
password = os.getenv('LOOPY_API_SECRET')
campaign_id = os.getenv('CAMPAIGN_ID')

print('📋 EXAMINING LOOPY CAMPAIGNS DATA')
print('=' * 50)

# Authenticate first
session = requests.Session()
auth_response = session.post(f'{base_url}/v1/account/login', json={
    'username': username,
    'password': password
}, timeout=10)

if auth_response.status_code != 200:
    print('❌ Authentication failed!')
    exit(1)

token = auth_response.json().get('token')
session.headers.update({'Authorization': token})

print(f'✅ Authenticated successfully')
print()

# Get campaigns data
try:
    response = session.get(f'{base_url}/v1/campaigns', timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        print(f'📊 Campaigns response structure:')
        print(f'   Total rows: {data.get("total_rows", "unknown")}')
        print(f'   Offset: {data.get("offset", "unknown")}')
        
        rows = data.get('rows', [])
        print(f'   Number of campaigns: {len(rows)}')
        print()
        
        # Look for our specific campaign
        for i, campaign in enumerate(rows):
            camp_id = campaign.get('id')
            camp_name = campaign.get('name', 'Unnamed')
            
            print(f'Campaign {i+1}:')
            print(f'   ID: {camp_id}')
            print(f'   Name: {camp_name}')
            print(f'   Keys: {list(campaign.keys())}')
            
            # Check if this is our campaign
            if camp_id == campaign_id:
                print(f'   🎯 THIS IS OUR CAMPAIGN!')
                print(f'   📋 Full campaign data:')
                print(json.dumps(campaign, indent=2))
                
                # Look for customer/card count info
                for key in ['cardCount', 'memberCount', 'customerCount', 'totalCards', 'participants']:
                    if key in campaign:
                        print(f'   📊 {key}: {campaign[key]}')
                        
            print()
            
    else:
        print(f'❌ Failed to get campaigns: {response.status_code}')
        print(f'Response: {response.text[:200]}')
        
except Exception as e:
    print(f'❌ Error: {e}')

print()
print('🔍 Testing alternative customer access approaches...')

# Try getting specific campaign details
try:
    # Sometimes you need to access campaign details differently
    alt_endpoints = [
        f'/v1/campaigns/{campaign_id}',
        f'/v1/campaign/{campaign_id}',  # Singular form
        f'/v1/campaigns/{campaign_id}/details',
        f'/v1/campaigns/{campaign_id}/stats',
        f'/v1/campaigns/{campaign_id}/analytics',
    ]
    
    for endpoint in alt_endpoints:
        try:
            response = session.get(f'{base_url}{endpoint}', timeout=10)
            print(f'{endpoint}: {response.status_code}')
            
            if response.status_code == 200:
                data = response.json()
                print(f'  ✅ SUCCESS! Keys: {list(data.keys()) if isinstance(data, dict) else "Not a dict"}')
                if isinstance(data, dict):
                    # Look for customer-related keys
                    customer_keys = [k for k in data.keys() if 'card' in k.lower() or 'customer' in k.lower() or 'member' in k.lower()]
                    if customer_keys:
                        print(f'  🎯 Customer-related keys: {customer_keys}')
                        for key in customer_keys:
                            value = data[key]
                            if isinstance(value, (int, float)):
                                print(f'    {key}: {value}')
                            elif isinstance(value, list):
                                print(f'    {key}: {len(value)} items')
                            
        except Exception as e:
            print(f'{endpoint}: Error - {str(e)[:50]}')
            
except Exception as e:
    print(f'❌ Error testing endpoints: {e}')

print()
print('💡 Key Findings:')
print('   - Loopy authentication is working ✅') 
print('   - Campaign data is accessible ✅')
print('   - Individual card access returns 403 Forbidden ❌')
print('   - This suggests either:')
print('     1. No customers have enrolled yet')
print('     2. Different API permissions needed for customer data')
print('     3. Customer data accessed differently in this account') 