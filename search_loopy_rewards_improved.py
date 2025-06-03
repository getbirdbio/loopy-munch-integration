#!/usr/bin/env python3
"""
Search Loopy Rewards - Improved Version
=======================================

Improved version with better error handling and authentication.
"""

import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv('production.env')

def search_loopy_rewards_improved():
    """Search for Loopy loyalty rewards with improved error handling"""
    
    print("🔍 IMPROVED LOOPY LOYALTY REWARDS SEARCH")
    print("=" * 60)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    # Loopy API Configuration
    loopy_api_key = os.getenv('LOOPY_API_KEY')
    loopy_username = os.getenv('LOOPY_USERNAME')
    loopy_base_url = os.getenv('LOOPY_BASE_URL', 'https://app.loopyloyalty.com/api')
    campaign_id = os.getenv('CAMPAIGN_ID')
    
    print(f"🔗 Loopy API: {loopy_base_url}")
    print(f"👤 Username: {loopy_username}")
    print(f"🎯 Campaign ID: {campaign_id}")
    print()
    
    # Headers with correct authentication (from debug, we know X-API-Key works)
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': loopy_api_key,
        'User-Agent': 'Loopy-Munch-Integration/1.0'
    }
    
    try:
        # Step 1: Get campaign details first
        print("🔍 Step 1: Getting campaign details...")
        
        campaign_url = f'{loopy_base_url}/campaigns/{campaign_id}'
        campaign_response = requests.get(campaign_url, headers=headers, timeout=10)
        
        print(f"   📡 GET {campaign_url}")
        print(f"   📊 Status: {campaign_response.status_code}")
        print(f"   📏 Response length: {len(campaign_response.text)}")
        
        if campaign_response.status_code == 200:
            try:
                campaign_data = campaign_response.json()
                print(f"   ✅ Campaign loaded successfully")
                print(f"   📋 Name: {campaign_data.get('name', 'Unknown')}")
                print(f"   📝 Description: {campaign_data.get('description', 'No description')}")
                
                # Show some campaign structure
                print(f"   🔧 Keys available: {list(campaign_data.keys())}")
                
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON decode error: {e}")
                print(f"   📄 Raw response: {campaign_response.text[:200]}...")
                return []
        else:
            print(f"   ❌ Failed to get campaign: {campaign_response.status_code}")
            print(f"   📄 Response: {campaign_response.text[:200]}...")
            return []
        
        # Step 2: Try different endpoints to find data
        endpoints_to_try = [
            f'/campaigns/{campaign_id}/transactions',
            f'/campaigns/{campaign_id}/rewards', 
            f'/campaigns/{campaign_id}/customers',
            f'/campaigns/{campaign_id}/activities',
            f'/campaigns/{campaign_id}/completions',
            f'/transactions',
            f'/rewards',
            f'/customers'
        ]
        
        print(f"\n🔍 Step 2: Testing data endpoints...")
        
        found_rewards = []
        
        for endpoint in endpoints_to_try:
            print(f"\n   📡 Testing: {endpoint}")
            
            # Calculate today's date range
            today = datetime.now().date()
            today_start = datetime.combine(today, datetime.min.time())
            today_end = datetime.combine(today, datetime.max.time())
            
            # Try with date parameters
            params = {
                'from': today_start.isoformat(),
                'to': today_end.isoformat(),
                'limit': 100,
                'campaign_id': campaign_id
            }
            
            try:
                url = f'{loopy_base_url}{endpoint}'
                response = requests.get(url, headers=headers, params=params, timeout=10)
                
                print(f"      📊 Status: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"      ✅ SUCCESS! Data loaded")
                        
                        if isinstance(data, list):
                            print(f"      📊 Found {len(data)} items")
                            
                            # Look for today's activities
                            today_items = []
                            for item in data:
                                item_date = item.get('created_at') or item.get('earned_at') or item.get('date')
                                if item_date and '2025-06-03' in str(item_date):
                                    today_items.append(item)
                                    
                                    # Check if it's a completed reward
                                    if 'reward' in endpoint or item.get('status') == 'earned':
                                        print(f"      🎉 Found reward: {item}")
                                        found_rewards.append(item)
                            
                            if today_items:
                                print(f"      📅 {len(today_items)} items from today")
                            else:
                                print(f"      📅 No items from today")
                                
                        elif isinstance(data, dict):
                            print(f"      📋 Dict with keys: {list(data.keys())}")
                            
                            # Check if there's a data array inside
                            if 'data' in data:
                                inner_data = data['data']
                                if isinstance(inner_data, list):
                                    print(f"      📊 Inner data has {len(inner_data)} items")
                        
                    except json.JSONDecodeError as e:
                        print(f"      ❌ JSON error: {e}")
                        print(f"      📄 Raw: {response.text[:100]}...")
                        
                elif response.status_code == 401:
                    print(f"      🔒 Authentication required")
                elif response.status_code == 403:
                    print(f"      🚫 Forbidden")
                elif response.status_code == 404:
                    print(f"      ❌ Not found")
                else:
                    print(f"      ⚠️ {response.status_code}: {response.text[:100]}...")
                    
            except Exception as e:
                print(f"      ❌ Error: {e}")
        
        # Step 3: Try to get customer data and check for completed stamps
        print(f"\n🔍 Step 3: Checking for completed stamp cards...")
        
        try:
            customers_url = f'{loopy_base_url}/campaigns/{campaign_id}/customers'
            customers_response = requests.get(customers_url, headers=headers, timeout=10)
            
            if customers_response.status_code == 200:
                customers_data = customers_response.json()
                print(f"   ✅ Got customers data")
                
                if isinstance(customers_data, list):
                    completed_today = []
                    
                    for customer in customers_data:
                        stamps = customer.get('stamps', 0)
                        customer_id = customer.get('id') or customer.get('customer_id')
                        
                        if stamps >= 12:  # Completed loyalty card
                            print(f"   🎉 Customer {customer_id} has {stamps} stamps (COMPLETED!)")
                            
                            completed_today.append({
                                'customer_id': customer_id,
                                'stamps': stamps,
                                'reward_type': 'Free Coffee',
                                'amount': 4000,  # R40
                                'earned_at': datetime.now().isoformat(),
                                'status': 'earned'
                            })
                    
                    if completed_today:
                        print(f"   🎯 Found {len(completed_today)} completed loyalty cards!")
                        found_rewards.extend(completed_today)
                    else:
                        print(f"   📊 No completed loyalty cards found")
                        
                elif isinstance(customers_data, dict) and 'data' in customers_data:
                    print(f"   📋 Customers data structure: {list(customers_data.keys())}")
                
            else:
                print(f"   ❌ Could not get customers: {customers_response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error getting customers: {e}")
        
        return found_rewards
        
    except Exception as e:
        print(f"❌ Error in rewards search: {e}")
        return []

def main():
    """Main function"""
    
    print("🔍 LOOPY LOYALTY REWARDS SEARCH - IMPROVED VERSION")
    print("=" * 70)
    print("🎯 Using correct API endpoint and authentication")
    print()
    
    # Search for rewards
    rewards = search_loopy_rewards_improved()
    
    # Show results
    print(f"\n📊 SEARCH RESULTS")
    print("=" * 30)
    
    if rewards:
        print(f"✅ Found {len(rewards)} rewards to process!")
        
        for i, reward in enumerate(rewards):
            print(f"\n   🎉 Reward {i+1}:")
            print(f"      Customer: {reward.get('customer_id', 'Unknown')}")
            print(f"      Type: {reward.get('reward_type', 'Unknown')}")
            print(f"      Amount: R{reward.get('amount', 0)/100}")
            print(f"      Status: {reward.get('status', 'Unknown')}")
        
        # Ask if we should process these rewards
        print(f"\n💰 PROCESSING OPTIONS:")
        print(f"   1. Process all {len(rewards)} rewards to Munch")
        print(f"   2. Show details only")
        
        try:
            from munch_loyalty_integration_final import deposit_loyalty_reward
            
            print(f"\n🚀 AUTO-PROCESSING TO MUNCH...")
            
            for reward in rewards:
                customer_id = reward['customer_id']
                amount = reward.get('amount', 4000)
                
                result = deposit_loyalty_reward(
                    customer_user_id=customer_id,
                    amount_in_cents=amount,
                    description=f"Loopy loyalty reward - {reward.get('reward_type', 'Free coffee')}"
                )
                
                if result['success']:
                    print(f"   ✅ {customer_id}: R{result['amount_deposited']} deposited")
                else:
                    print(f"   ❌ {customer_id}: {result['error']}")
                    
        except ImportError:
            print("   ⚠️ Munch integration not available")
            
    else:
        print(f"ℹ️ No rewards found for today")
        print(f"💡 This could mean:")
        print(f"   - No customers completed loyalty cards today")
        print(f"   - Rewards were already processed")
        print(f"   - Different date range needed")

if __name__ == "__main__":
    main() 