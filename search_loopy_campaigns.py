#!/usr/bin/env python3
"""
Search Loopy Campaigns
======================

Explore the /campaigns endpoint to find our campaign and search for rewards.
"""

import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv('production.env')

def get_loopy_token():
    """Get working JWT token"""
    
    loopy_username = os.getenv('LOOPY_USERNAME')
    loopy_api_secret = os.getenv('LOOPY_API_SECRET')
    
    login_data = {
        'username': loopy_username,
        'password': loopy_api_secret
    }
    
    response = requests.post(
        'https://api.loopyloyalty.com/v1/account/login',
        json=login_data,
        headers={'Content-Type': 'application/json'},
        timeout=10
    )
    
    if response.status_code == 200:
        return response.json().get('token')
    return None

def search_campaigns_and_rewards():
    """Search campaigns for our target campaign and look for rewards"""
    
    print("🎯 SEARCHING LOOPY CAMPAIGNS FOR REWARDS")
    print("=" * 60)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}")
    print()
    
    token = get_loopy_token()
    if not token:
        print("❌ Could not get authentication token")
        return []
    
    headers = {
        'Authorization': token,
        'Content-Type': 'application/json'
    }
    
    base_url = 'https://api.loopyloyalty.com/v1'
    target_campaign_id = os.getenv('CAMPAIGN_ID')
    
    print(f"🎯 Target Campaign ID: {target_campaign_id}")
    print()
    
    try:
        # Step 1: Get all campaigns
        print("🔍 Step 1: Getting all campaigns...")
        
        campaigns_response = requests.get(f'{base_url}/campaigns', headers=headers, timeout=10)
        
        if campaigns_response.status_code != 200:
            print(f"❌ Failed to get campaigns: {campaigns_response.status_code}")
            return []
        
        campaigns_data = campaigns_response.json()
        print(f"✅ Campaigns data retrieved")
        print(f"📊 Structure: {list(campaigns_data.keys())}")
        print(f"📈 Total rows: {campaigns_data.get('total_rows', 0)}")
        print(f"📄 Offset: {campaigns_data.get('offset', 0)}")
        print()
        
        # Get the campaigns list
        campaigns = campaigns_data.get('rows', [])
        print(f"🎯 Found {len(campaigns)} campaigns:")
        
        target_campaign = None
        
        for i, campaign in enumerate(campaigns):
            campaign_id = campaign.get('id', 'No ID')
            campaign_name = campaign.get('name', 'No name')
            campaign_status = campaign.get('status', 'Unknown')
            
            print(f"   {i+1}. {campaign_name}")
            print(f"      ID: {campaign_id}")
            print(f"      Status: {campaign_status}")
            
            # Show available keys for the first campaign
            if i == 0:
                print(f"      Available keys: {list(campaign.keys())}")
            
            # Check if this is our target campaign
            if campaign_id == target_campaign_id:
                print(f"      🎉 FOUND TARGET CAMPAIGN!")
                target_campaign = campaign
            
            print()
        
        if not target_campaign:
            print(f"❌ Target campaign {target_campaign_id} not found")
            print(f"💡 Available campaign IDs:")
            for campaign in campaigns:
                print(f"   - {campaign.get('id', 'No ID')}")
            return []
        
        # Step 2: Explore the target campaign in detail
        print(f"🔍 Step 2: Exploring target campaign details...")
        print("-" * 50)
        
        print(f"📋 Campaign Details:")
        for key, value in target_campaign.items():
            if isinstance(value, (str, int, float, bool)):
                print(f"   {key}: {value}")
            elif isinstance(value, dict):
                print(f"   {key}: (dict with {len(value)} keys)")
            elif isinstance(value, list):
                print(f"   {key}: (list with {len(value)} items)")
            else:
                print(f"   {key}: {type(value)}")
        
        # Step 3: Try to access campaign-specific endpoints
        print(f"\n🔍 Step 3: Accessing campaign-specific data...")
        print("-" * 50)
        
        campaign_endpoints = [
            f'/campaign/{target_campaign_id}',
            f'/campaigns/{target_campaign_id}',
            f'/campaigns/{target_campaign_id}/cards',
            f'/campaigns/{target_campaign_id}/customers',
            f'/campaigns/{target_campaign_id}/analytics',
            f'/campaigns/{target_campaign_id}/rewards',
            f'/campaigns/{target_campaign_id}/transactions',
            f'/campaigns/{target_campaign_id}/enrollments',
            f'/campaigns/{target_campaign_id}/stamps',
            f'/campaign/{target_campaign_id}/cards',
            f'/campaign/{target_campaign_id}/customers',
        ]
        
        working_data = {}
        
        for endpoint in campaign_endpoints:
            try:
                url = f'{base_url}{endpoint}'
                response = requests.get(url, headers=headers, timeout=10)
                
                print(f"   📡 {endpoint}: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        working_data[endpoint] = data
                        
                        print(f"      ✅ SUCCESS!")
                        
                        if isinstance(data, dict):
                            print(f"      📋 Keys: {list(data.keys())}")
                            
                            # Look for today's data
                            if 'rows' in data:
                                rows = data['rows']
                                print(f"      📊 Found {len(rows)} rows")
                                
                                # Check for recent activity
                                today = datetime.now().strftime('%Y-%m-%d')
                                recent_items = []
                                
                                for item in rows:
                                    # Look for date fields
                                    for date_field in ['created', 'updated', 'earned', 'lastStampEarned', 'createTime']:
                                        item_date = item.get(date_field, '')
                                        if today in str(item_date):
                                            recent_items.append(item)
                                            break
                                
                                if recent_items:
                                    print(f"      📅 {len(recent_items)} items from today!")
                                    
                                    # Look for completed loyalty cards
                                    for item in recent_items:
                                        stamps = item.get('totalStampsEarned', 0)
                                        if stamps >= 12:
                                            print(f"      🎉 COMPLETED CARD: {item.get('id')} ({stamps} stamps)")
                                
                        elif isinstance(data, list):
                            print(f"      📊 List with {len(data)} items")
                            
                        # Don't continue if we found good data
                        break
                        
                    except json.JSONDecodeError:
                        print(f"      📄 Non-JSON response")
                        
                elif response.status_code == 403:
                    print(f"      🔒 Forbidden")
                elif response.status_code == 404:
                    print(f"      ❌ Not found")
                    
            except Exception as e:
                print(f"      ❌ Error: {e}")
        
        # Step 4: Analyze any working data for rewards
        print(f"\n🔍 Step 4: Analyzing data for completed rewards...")
        print("-" * 50)
        
        found_rewards = []
        
        for endpoint, data in working_data.items():
            print(f"\n📊 Analyzing {endpoint}:")
            
            if isinstance(data, dict) and 'rows' in data:
                rows = data['rows']
                
                for item in rows:
                    # Check if this looks like a loyalty card
                    stamps = item.get('totalStampsEarned', 0)
                    total_rewards = item.get('totalRewardsEarned', 0)
                    card_id = item.get('id')
                    
                    if stamps >= 12:  # Completed loyalty card
                        print(f"   🎉 COMPLETED CARD FOUND!")
                        print(f"      Card ID: {card_id}")
                        print(f"      Stamps: {stamps}")
                        print(f"      Rewards earned: {total_rewards}")
                        print(f"      Last stamp: {item.get('lastStampEarnedDate', 'Unknown')}")
                        
                        found_rewards.append({
                            'customer_id': card_id,
                            'stamps': stamps,
                            'rewards_earned': total_rewards,
                            'reward_type': 'Free Coffee',
                            'amount': 4000,  # R40
                            'source': 'loopy_campaigns_api',
                            'last_stamp': item.get('lastStampEarnedDate'),
                            'card_data': item
                        })
        
        return found_rewards
        
    except Exception as e:
        print(f"❌ Error in campaign search: {e}")
        return []

def process_found_rewards(rewards):
    """Process any found rewards"""
    
    if not rewards:
        print(f"\n📊 SEARCH RESULTS")
        print("=" * 30)
        print("ℹ️ No completed loyalty cards found")
        print("💡 This means:")
        print("   - No customers have 12+ stamps today")
        print("   - All rewards may already be processed")
        print("   - Customers are still working toward completion")
        return
    
    print(f"\n🎉 FOUND {len(rewards)} COMPLETED LOYALTY REWARDS!")
    print("=" * 60)
    
    for i, reward in enumerate(rewards):
        print(f"\n   🎯 Reward {i+1}:")
        print(f"      Customer/Card ID: {reward['customer_id']}")
        print(f"      Stamps Earned: {reward['stamps']}")
        print(f"      Rewards Earned: {reward['rewards_earned']}")
        print(f"      Value: R{reward['amount']/100}")
        print(f"      Last Stamp: {reward.get('last_stamp', 'Unknown')}")
    
    # Try to process with Munch
    try:
        from munch_loyalty_integration_final import deposit_loyalty_reward
        
        print(f"\n💰 PROCESSING REWARDS TO MUNCH...")
        print("-" * 40)
        
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
        print(f"🎉 {successful} customers now have FREE coffee credits!")
        
    except ImportError:
        print(f"\n⚠️ Munch integration not available")
        print(f"💡 Found rewards can be manually processed")

def main():
    """Main function"""
    
    print("🎯 LOOPY LOYALTY CAMPAIGNS & REWARDS SEARCH")
    print("=" * 70)
    print("🔍 Using working /campaigns endpoint to find rewards")
    print()
    
    # Search campaigns and rewards
    rewards = search_campaigns_and_rewards()
    
    # Process any found rewards
    process_found_rewards(rewards)
    
    print(f"\n🏁 CAMPAIGN SEARCH COMPLETE")
    print("=" * 30)
    print("✅ Loopy campaigns explored")
    print("🔍 Rewards search performed") 
    print("💡 System ready for regular monitoring")

if __name__ == "__main__":
    main() 