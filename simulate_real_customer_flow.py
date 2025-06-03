#!/usr/bin/env python3
"""
Simulate Real Customer Flow
==========================

Simulate the complete flow of a customer getting stamps and earning free coffee
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5008"

def simulate_customer_journey():
    """Simulate a customer's complete loyalty journey"""
    print("☕ SIMULATING REAL CUSTOMER JOURNEY")
    print("=" * 60)
    
    # Customer data
    customer = {
        "id": "cRealCustomer456",
        "name": "Sarah Coffee Lover",
        "email": "sarah@coffeelover.com",
        "phone": "+27821234567"
    }
    
    print(f"👤 Customer: {customer['name']}")
    print(f"📧 Email: {customer['email']}")
    print(f"📞 Phone: {customer['phone']}")
    print(f"🎫 Loyalty ID: {customer['id']}")
    print()
    
    # Journey stages
    stages = [
        {"visit": 1, "stamps": 3, "action": "First visit - 3 coffees"},
        {"visit": 2, "stamps": 7, "action": "Second visit - 4 more coffees"},
        {"visit": 3, "stamps": 11, "action": "Third visit - 4 more coffees"}, 
        {"visit": 4, "stamps": 12, "action": "Fourth visit - 1 coffee (FREE COFFEE EARNED!)"},
        {"visit": 5, "stamps": 18, "action": "Fifth visit - 6 more coffees"},
        {"visit": 6, "stamps": 24, "action": "Sixth visit - 6 more coffees (2nd FREE COFFEE!)"}
    ]
    
    for stage in stages:
        print(f"🛍️ Visit {stage['visit']}: {stage['action']}")
        print(f"   📍 Total stamps: {stage['stamps']}")
        
        # Send stamp/rewards webhook
        webhook_data = {
            "event": "rewards.updated" if stage['stamps'] >= 12 else "stamp.added",
            "timestamp": datetime.now().isoformat(),
            "card": {
                "id": customer['id'],
                "totalStampsEarned": stage['stamps'],
                "totalRewardsEarned": stage['stamps'] // 12,
                "totalRewardsRedeemed": 0,
                "customerDetails": {
                    "Name": customer['name'],
                    "Email address": customer['email'],
                    "Contact Number": customer['phone']
                },
                "passStatus": "active"
            }
        }
        
        # Determine endpoint based on whether customer earned rewards
        if stage['stamps'] >= 12 and stage['stamps'] % 12 == 0:
            endpoint = "/webhook/loopy/rewards"
            print("   🎁 Sending to REWARDS webhook (customer earned free coffee!)")
        else:
            endpoint = "/webhook/loopy/stamp"
            print("   📍 Sending to STAMP webhook")
        
        try:
            response = requests.post(
                f"{BASE_URL}{endpoint}",
                json=webhook_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'free_coffees' in data and data['free_coffees'] > 0:
                    print(f"   🎉 SUCCESS! Customer earned {data['free_coffees']} free coffee(s)!")
                    print(f"   💰 Credit applied: R{data['credit_amount']}")
                    print(f"   📤 Forwarded to Make.com: {'✅' if data.get('forwarded_to_make', {}).get('success') else '❌'}")
                else:
                    free_coffees_available = stage['stamps'] // 12
                    stamps_needed = 12 - (stage['stamps'] % 12)
                    if free_coffees_available > 0:
                        print(f"   💡 Customer has {free_coffees_available} free coffee(s) available")
                    if stamps_needed < 12:
                        print(f"   📈 Needs {stamps_needed} more stamps for next free coffee")
                    
                print(f"   ✅ Webhook processed successfully")
                
            else:
                print(f"   ❌ Webhook failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        time.sleep(1)  # Simulate time between visits
    
    print("=" * 60)
    print("📊 CUSTOMER JOURNEY SUMMARY")
    print("=" * 60)
    final_stamps = stages[-1]['stamps']
    total_free_coffees = final_stamps // 12
    total_credit = total_free_coffees * 40
    
    print(f"👤 Customer: {customer['name']}")
    print(f"📍 Total stamps earned: {final_stamps}")
    print(f"☕ Total free coffees earned: {total_free_coffees}")
    print(f"💰 Total credit value: R{total_credit}")
    print(f"🎁 Current balance: R{total_credit} (if not yet redeemed)")
    
    print("\n🔄 Integration Flow:")
    print("1. ✅ Customer gets stamped at coffee shop")
    print("2. ✅ Loopy sends webhook to our integration service")
    print("3. ✅ Service calculates free coffees and credit amount")
    print("4. ✅ Service forwards enriched data to Make.com")
    print("5. ✅ Make.com applies credit to Munch POS system")
    print("6. ✅ Customer can use credit immediately for purchases")
    
    print("\n🎯 Next Steps:")
    print("- Configure Make.com scenario to process the webhook data")
    print("- Set up Make.com to call Munch API with customer credit")
    print("- Test with real customer stamping in coffee shop")
    
    return True

if __name__ == "__main__":
    simulate_customer_journey() 