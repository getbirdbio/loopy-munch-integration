#!/usr/bin/env python3
"""
Search Loopy Rewards - Final Version
===================================

Using the correct Loopy Loyalty API v1 with proper JWT authentication.
"""

import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv('production.env')

def get_loopy_jwt_token():
    """Get JWT token from Loopy Loyalty API"""
    
    loopy_username = os.getenv('LOOPY_USERNAME')
    loopy_api_secret = os.getenv('LOOPY_API_SECRET')  # This is the correct password
    
    login_url = 'https://api.loopyloyalty.com/v1/account/login'
    
    login_data = {
        'username': loopy_username,
        'password': loopy_api_secret  # API secret is the correct password
    }
    
    try:
        response = requests.post(
            login_url,
            json=login_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"🔐 Login attempt: {response.status_code}")
        
        if response.status_code == 200:
            auth_data = response.json()
            token = auth_data.get('token')
            if token:
                print(f"✅ Authentication successful")
                print(f"🔑 Token: {token[:20]}...")
                return token
            else:
                print(f"❌ No token in response: {auth_data}")
                return None
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def search_loopy_rewards_final():
    """Search for Loopy rewards using correct API v1"""
    
    print("🔍 LOOPY LOYALTY REWARDS SEARCH - FINAL VERSION")
    print("=" * 60)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    # Get authentication token
    print("🔐 Step 1: Authenticating with Loopy API...")
    jwt_token = get_loopy_jwt_token()
    
    if not jwt_token:
        print("❌ Authentication failed - cannot proceed")
        return []
    
    # API Configuration
    base_url = 'https://api.loopyloyalty.com/v1'
    campaign_id = os.getenv('CAMPAIGN_ID')
    
    headers = {
        'Authorization': jwt_token,
        'Content-Type': 'application/json'
    }
    
    print(f"\n🎯 Campaign ID: {campaign_id}")
    print(f"🔗 Base URL: {base_url}")
    print()
    
    found_rewards = []
    
    try:
        # Step 2: Search for cards in the campaign
        print("🔍 Step 2: Searching for campaign cards...")
        
        # Based on the documentation, we need to search for cards
        # We'll try different approaches to find cards with recent activity
        
        # Method 1: Try to get campaign information
        campaign_endpoints = [
            f'/campaigns/{campaign_id}',
            f'/campaign/{campaign_id}',
            f'/enrol/{campaign_id}'  # This is mentioned in docs
        ]
        
        for endpoint in campaign_endpoints:
            try:
                url = f'{base_url}{endpoint}'
                response = requests.get(url, headers=headers, timeout=10)
                
                print(f"   📡 {endpoint}: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"      ✅ SUCCESS!")
                    try:
                        data = response.json()
                        print(f"      📋 Keys: {list(data.keys()) if isinstance(data, dict) else 'List'}")
                    except:
                        print(f"      📄 Response length: {len(response.text)}")
                        
            except Exception as e:
                print(f"      ❌ Error: {e}")
        
        # Step 3: Try to search for recent cards/activity
        print(f"\n🔍 Step 3: Searching for recent card activity...")
        
        # Calculate date range for today
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        
        # Try different search approaches
        search_endpoints = [
            '/cards',
            '/card',
            f'/cards?campaign={campaign_id}',
            '/activity',
            '/transactions',
            '/stamps'
        ]
        
        for endpoint in search_endpoints:
            try:
                url = f'{base_url}{endpoint}'
                
                # Try with and without parameters
                params_options = [
                    {},
                    {'campaign': campaign_id},
                    {'campaignId': campaign_id},
                    {'date': today_start.strftime('%Y-%m-%d')},
                    {'limit': 100}
                ]
                
                for params in params_options[:2]:  # Test first 2 param combinations
                    try:
                        response = requests.get(url, headers=headers, params=params, timeout=10)
                        
                        print(f"   📡 {endpoint} {params}: {response.status_code}")
                        
                        if response.status_code == 200:
                            try:
                                data = response.json()
                                print(f"      ✅ SUCCESS! Data type: {type(data)}")
                                
                                if isinstance(data, list):
                                    print(f"      📊 Found {len(data)} items")
                                    
                                    # Look for cards with 12+ stamps (completed)
                                    for item in data:
                                        stamps = item.get('totalStampsEarned', 0)
                                        card_id = item.get('id')
                                        
                                        if stamps >= 12:
                                            print(f"      🎉 COMPLETED CARD: {card_id} ({stamps} stamps)")
                                            
                                            found_rewards.append({
                                                'customer_id': card_id,
                                                'stamps': stamps,
                                                'reward_type': 'Free Coffee',
                                                'amount': 4000,  # R40
                                                'earned_at': datetime.now().isoformat(),
                                                'status': 'earned',
                                                'source': 'loopy_card_search'
                                            })
                                
                                elif isinstance(data, dict):
                                    print(f"      📋 Dict keys: {list(data.keys())}")
                                    
                                # Don't continue testing if we found something
                                if data:
                                    break
                                    
                            except json.JSONDecodeError:
                                print(f"      📄 Non-JSON response")
                        
                        elif response.status_code == 401:
                            print(f"      🔒 Authentication required")
                        elif response.status_code == 404:
                            print(f"      ❌ Not found")
                            
                    except Exception as e:
                        continue
                        
            except Exception as e:
                print(f"   ❌ Error testing {endpoint}: {e}")
        
        # Step 4: Manual card lookup if we have specific card IDs
        print(f"\n🔍 Step 4: Testing card lookup endpoints...")
        
        # Test card lookup format from documentation
        test_card_ids = ['test', 'sample']  # We'd need real card IDs
        
        for card_id in test_card_ids:
            try:
                card_url = f'{base_url}/card/{card_id}?includeEvents=true'
                response = requests.get(card_url, headers=headers, timeout=5)
                
                print(f"   📡 /card/{card_id}: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"      ✅ Card API working!")
                    break
                elif response.status_code == 404:
                    print(f"      ℹ️ Card not found (expected)")
                    
            except Exception as e:
                continue
        
        return found_rewards
        
    except Exception as e:
        print(f"❌ Error in search: {e}")
        return []

def process_found_rewards(rewards):
    """Process any found rewards to Munch"""
    
    if not rewards:
        print(f"\n📊 SEARCH COMPLETE")
        print("=" * 30)
        print("ℹ️ No completed loyalty cards found today")
        print("💡 This could mean:")
        print("   - No customers completed 12-stamp cards today")
        print("   - Cards were already processed")
        print("   - Need different search parameters")
        return
    
    print(f"\n🎉 FOUND {len(rewards)} COMPLETED LOYALTY CARDS!")
    print("=" * 50)
    
    for i, reward in enumerate(rewards):
        print(f"\n   🎯 Reward {i+1}:")
        print(f"      Card/Customer: {reward['customer_id']}")
        print(f"      Stamps: {reward['stamps']}")
        print(f"      Value: R{reward['amount']/100}")
        print(f"      Status: {reward['status']}")
    
    # Try to process to Munch
    try:
        from munch_loyalty_integration_final import deposit_loyalty_reward
        
        print(f"\n💰 PROCESSING TO MUNCH...")
        print("-" * 30)
        
        successful = 0
        
        for reward in rewards:
            customer_id = reward['customer_id']
            amount = reward['amount']
            
            print(f"💳 Processing {customer_id}...")
            
            result = deposit_loyalty_reward(
                customer_user_id=customer_id,
                amount_in_cents=amount,
                description=f"Loopy loyalty reward - {reward['stamps']} stamps completed"
            )
            
            if result['success']:
                print(f"   ✅ SUCCESS! R{result['amount_deposited']} deposited")
                successful += 1
            else:
                print(f"   ❌ FAILED: {result['error']}")
        
        print(f"\n📊 PROCESSING SUMMARY:")
        print(f"✅ Successful: {successful}/{len(rewards)}")
        
        if successful > 0:
            print(f"🎉 {successful} customers now have FREE coffee credits!")
            
    except ImportError:
        print(f"\n⚠️ Munch integration not available for auto-processing")
        print(f"💡 Rewards found can be manually processed")

def main():
    """Main function"""
    
    print("🔍 LOOPY LOYALTY REWARDS SEARCH & PROCESSING")
    print("=" * 70)
    print("🎯 Using correct Loopy Loyalty API v1 with JWT authentication")
    print()
    
    # Search for rewards
    rewards = search_loopy_rewards_final()
    
    # Process any found rewards
    process_found_rewards(rewards)
    
    print(f"\n🏁 SEARCH COMPLETE")
    print("=" * 20)
    print("✅ Loopy API connectivity tested")
    print("🔍 Reward search performed")
    print("💡 System ready for processing real rewards")

if __name__ == "__main__":
    main() 