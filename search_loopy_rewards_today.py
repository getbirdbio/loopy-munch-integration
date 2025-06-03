#!/usr/bin/env python3
"""
Search Loopy Rewards Today
==========================

Searches the Loopy Loyalty system for any rewards earned today
that can be processed and uploaded as credits to Munch.
"""

import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv('production.env')

def search_loopy_rewards_today():
    """Search for Loopy loyalty rewards earned today"""
    
    print("🔍 SEARCHING LOOPY LOYALTY SYSTEM FOR TODAY'S REWARDS")
    print("=" * 60)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    # Loopy API Configuration
    loopy_api_key = os.getenv('LOOPY_API_KEY')
    loopy_username = os.getenv('LOOPY_USERNAME')
    loopy_base_url = os.getenv('LOOPY_BASE_URL', 'https://app.loopyloyalty.com/api')
    campaign_id = os.getenv('CAMPAIGN_ID')
    
    if not all([loopy_api_key, loopy_username, campaign_id]):
        print("❌ Missing Loopy API configuration")
        return []
    
    print(f"🔗 Loopy API: {loopy_base_url}")
    print(f"👤 Username: {loopy_username}")
    print(f"🎯 Campaign ID: {campaign_id}")
    print()
    
    # Calculate today's date range
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    print(f"📅 Searching from: {today_start.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 Searching to: {today_end.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {loopy_api_key}'
    }
    
    try:
        # Search for recent loyalty activity
        print("🔍 Step 1: Searching for recent loyalty transactions...")
        
        # Get campaign details first
        campaign_response = requests.get(
            f'{loopy_base_url}/campaigns/{campaign_id}',
            headers=headers,
            timeout=10
        )
        
        if campaign_response.status_code == 200:
            campaign_data = campaign_response.json()
            print(f"✅ Campaign found: {campaign_data.get('name', 'Unknown')}")
            print(f"   Description: {campaign_data.get('description', 'No description')}")
            print()
        else:
            print(f"⚠️ Could not fetch campaign details: {campaign_response.status_code}")
        
        # Search for transactions in the campaign
        print("🔍 Step 2: Searching for transactions...")
        
        transactions_response = requests.get(
            f'{loopy_base_url}/campaigns/{campaign_id}/transactions',
            headers=headers,
            params={
                'from': today_start.isoformat(),
                'to': today_end.isoformat(),
                'limit': 100
            },
            timeout=10
        )
        
        if transactions_response.status_code == 200:
            transactions = transactions_response.json()
            print(f"✅ Found {len(transactions)} transactions today")
            
            if transactions:
                print(f"\n📊 TODAY'S TRANSACTIONS:")
                for i, txn in enumerate(transactions):
                    txn_time = txn.get('created_at', 'Unknown time')
                    customer_id = txn.get('customer_id', 'Unknown')
                    points = txn.get('points', 0)
                    stamps = txn.get('stamps', 0)
                    
                    print(f"   {i+1}. Time: {txn_time}")
                    print(f"      Customer: {customer_id}")
                    print(f"      Points: {points}, Stamps: {stamps}")
                    print()
            else:
                print("   No transactions found today")
        else:
            print(f"❌ Failed to get transactions: {transactions_response.status_code}")
            print(f"   Response: {transactions_response.text[:200]}")
        
        # Search for completed loyalty cards (rewards)
        print("🔍 Step 3: Searching for completed loyalty cards...")
        
        rewards_response = requests.get(
            f'{loopy_base_url}/campaigns/{campaign_id}/rewards',
            headers=headers,
            params={
                'from': today_start.isoformat(),
                'to': today_end.isoformat(),
                'status': 'earned',
                'limit': 100
            },
            timeout=10
        )
        
        completed_rewards = []
        
        if rewards_response.status_code == 200:
            rewards = rewards_response.json()
            print(f"✅ Found {len(rewards)} completed rewards today")
            
            if rewards:
                print(f"\n🎉 TODAY'S COMPLETED REWARDS:")
                for i, reward in enumerate(rewards):
                    customer_id = reward.get('customer_id', 'Unknown')
                    reward_type = reward.get('reward_type', 'Unknown')
                    earned_at = reward.get('earned_at', 'Unknown time')
                    status = reward.get('status', 'Unknown')
                    
                    print(f"   {i+1}. Customer: {customer_id}")
                    print(f"      Reward: {reward_type}")
                    print(f"      Earned: {earned_at}")
                    print(f"      Status: {status}")
                    
                    # Check if this is a free coffee reward
                    if 'coffee' in reward_type.lower() or 'free' in reward_type.lower():
                        completed_rewards.append({
                            'customer_id': customer_id,
                            'reward_type': reward_type,
                            'earned_at': earned_at,
                            'status': status,
                            'amount': 4000  # R40 for free coffee
                        })
                        print(f"      ✅ Eligible for R40 Munch credit!")
                    
                    print()
                    
            else:
                print("   No completed rewards found today")
        else:
            print(f"❌ Failed to get rewards: {rewards_response.status_code}")
            print(f"   Response: {rewards_response.text[:200]}")
        
        # Search for customers with high stamp counts
        print("🔍 Step 4: Searching for customers near completion...")
        
        customers_response = requests.get(
            f'{loopy_base_url}/campaigns/{campaign_id}/customers',
            headers=headers,
            params={
                'limit': 100,
                'min_stamps': 10  # Customers with 10+ stamps (close to 12)
            },
            timeout=10
        )
        
        if customers_response.status_code == 200:
            customers = customers_response.json()
            print(f"✅ Found {len(customers)} customers near completion")
            
            if customers:
                print(f"\n⭐ CUSTOMERS CLOSE TO COMPLETION:")
                for i, customer in enumerate(customers):
                    customer_id = customer.get('id', 'Unknown')
                    stamps = customer.get('stamps', 0)
                    points = customer.get('points', 0)
                    
                    if stamps >= 12:
                        status = "🎉 COMPLETED! (Eligible for reward)"
                        completed_rewards.append({
                            'customer_id': customer_id,
                            'stamps': stamps,
                            'points': points,
                            'amount': 4000  # R40 for free coffee
                        })
                    elif stamps >= 10:
                        status = f"⭐ {stamps}/12 stamps (Close!)"
                    else:
                        status = f"📊 {stamps}/12 stamps"
                    
                    print(f"   {i+1}. Customer: {customer_id}")
                    print(f"      Stamps: {stamps}, Points: {points}")
                    print(f"      Status: {status}")
                    print()
        else:
            print(f"❌ Failed to get customers: {customers_response.status_code}")
        
        return completed_rewards
        
    except Exception as e:
        print(f"❌ Error searching Loopy system: {e}")
        return []

def process_loopy_rewards_to_munch(rewards):
    """Process found Loopy rewards and upload credits to Munch"""
    
    if not rewards:
        print("\n📊 PROCESSING RESULTS")
        print("=" * 40)
        print("ℹ️  No rewards found to process today")
        return
    
    print(f"\n💰 PROCESSING {len(rewards)} REWARDS TO MUNCH")
    print("=" * 50)
    
    try:
        # Import our production integration
        from munch_loyalty_integration_final import deposit_loyalty_reward
        
        successful_deposits = []
        failed_deposits = []
        
        for i, reward in enumerate(rewards):
            customer_id = reward['customer_id']
            amount = reward.get('amount', 4000)  # Default R40
            
            print(f"💳 Processing {i+1}/{len(rewards)}: Customer {customer_id}")
            print(f"   Amount: R{amount/100}")
            
            # Check if customer exists in Munch first
            result = deposit_loyalty_reward(
                customer_user_id=customer_id,
                amount_in_cents=amount,
                description=f"Loopy loyalty reward - {reward.get('reward_type', 'Free coffee')}"
            )
            
            if result['success']:
                print(f"   ✅ SUCCESS! R{result['amount_deposited']} deposited")
                print(f"   🆔 Deposit ID: {result.get('deposit_id', 'N/A')}")
                successful_deposits.append(result)
            else:
                print(f"   ❌ FAILED: {result['error']}")
                failed_deposits.append({
                    'customer_id': customer_id,
                    'error': result['error']
                })
            
            print()
        
        # Summary
        print("📊 PROCESSING SUMMARY")
        print("=" * 30)
        print(f"✅ Successful: {len(successful_deposits)}")
        print(f"❌ Failed: {len(failed_deposits)}")
        
        if successful_deposits:
            total_deposited = sum(d['amount_deposited'] for d in successful_deposits)
            print(f"💰 Total deposited: R{total_deposited}")
            print(f"🎉 Customers now have FREE coffee credits!")
        
        if failed_deposits:
            print(f"\n⚠️ FAILED DEPOSITS:")
            for failure in failed_deposits:
                print(f"   Customer {failure['customer_id']}: {failure['error']}")
        
        return successful_deposits
        
    except ImportError:
        print("❌ Could not import Munch integration module")
        return []
    except Exception as e:
        print(f"❌ Error processing rewards: {e}")
        return []

def main():
    """Main function to search and process Loopy rewards"""
    
    print("🔍 LOOPY LOYALTY REWARDS SEARCH & PROCESSING")
    print("=" * 60)
    print("🎯 Finding today's rewards to upload to Munch")
    print()
    
    # Search for today's rewards
    rewards = search_loopy_rewards_today()
    
    # Process any found rewards
    if rewards:
        deposits = process_loopy_rewards_to_munch(rewards)
        
        if deposits:
            print(f"\n🎉 SUCCESS!")
            print(f"✅ {len(deposits)} rewards processed successfully")
            print(f"💳 Credits uploaded to Munch accounts")
            print(f"☕ Customers can now get FREE coffee!")
        else:
            print(f"\n⚠️ Found rewards but processing failed")
    else:
        print(f"\n📊 SEARCH COMPLETE")
        print(f"ℹ️  No pending rewards found for today")
        print(f"🔄 Check again later or tomorrow for new completions")

if __name__ == "__main__":
    main() 