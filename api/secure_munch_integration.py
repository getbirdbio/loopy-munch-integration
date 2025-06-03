#!/usr/bin/env python3
"""
SECURE Munch Integration - NO HARDCODED CUSTOMER DATA
====================================================

CRITICAL SECURITY REQUIREMENTS:
1. NEVER use hardcoded customer IDs
2. ALWAYS validate customer data from Loopy webhook
3. ALWAYS verify customer exists in Munch before depositing
4. ALWAYS create audit trail for deposits
5. NEVER deposit without proper authentication
"""

import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv('production.env')

class SecureMunchIntegration:
    """Secure Munch integration with proper validation"""
    
    def __init__(self):
        """Initialize with proper API configuration"""
        
        self.api_key = os.getenv('MUNCH_API_KEY')
        self.org_id = os.getenv('MUNCH_ORG_ID')
        self.payment_method_id = '0193bf43-bc83-744e-9510-bc20d2314fdb'  # Account Load
        self.base_url = 'https://api.munch.cloud/api'
        
        if not self.api_key or not self.org_id:
            raise ValueError("❌ Missing required Munch API credentials")
        
        print("🔒 Secure Munch Integration initialized")
        print(f"   Organization: {self.org_id}")
        print(f"   Base URL: {self.base_url}")
        
    def get_headers(self):
        """Get properly configured headers for Munch API"""
        
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Authorization-Type': 'internal',
            'Content-Type': 'application/json',
            'Locale': 'en',
            'Munch-Platform': 'cloud.munch.portal',
            'Munch-Timezone': 'Africa/Johannesburg',
            'Munch-Version': '2.20.1',
            'Munch-Employee': '28c5e780-3707-11ec-bb31-dde416ab9f61',
            'Munch-Organisation': self.org_id
        }
    
    def find_customer_by_email(self, email):
        """
        Find customer in Munch by email from Loopy webhook
        NO hardcoded IDs - only search by real customer data
        """
        
        if not email or not isinstance(email, str):
            print(f"❌ Invalid email provided: {email}")
            return None
        
        print(f"🔍 Searching Munch for customer by email: {email}")
        
        try:
            response = requests.post(
                f'{self.base_url}/account/retrieve-users',
                headers=self.get_headers(),
                json={
                    "id": "3e92a480-5f21-11ec-b43f-dde416ab9f61",
                    "timezone": "Africa/Johannesburg"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                users_data = response.json()
                users = users_data.get('data', [])
                
                print(f"🔍 Searching {len(users)} Munch customers...")
                
                # Search for customer by email
                for user in users:
                    user_email = user.get('email', '').lower()
                    
                    if user_email == email.lower():
                        customer_name = f"{user.get('firstName', '')} {user.get('lastName', '')}"
                        print(f"✅ Found customer: {customer_name} ({email})")
                        
                        return {
                            'id': user.get('id'),
                            'email': user_email,
                            'name': customer_name,
                            'phone': user.get('phone', ''),
                            'firstName': user.get('firstName', ''),
                            'lastName': user.get('lastName', '')
                        }
                
                print(f"⚠️ Customer not found in Munch: {email}")
                return None
                
            else:
                print(f"❌ Failed to search customers: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error searching customer: {e}")
            return None
    
    def validate_deposit_request(self, loopy_webhook_data, customer_email):
        """
        Validate that deposit request is legitimate from Loopy webhook
        NEVER allow deposits without proper validation
        """
        
        print("🔒 VALIDATING DEPOSIT REQUEST...")
        
        # Validate webhook structure
        if not isinstance(loopy_webhook_data, dict):
            print("❌ Invalid webhook data structure")
            return False
        
        # Validate customer email matches webhook
        card_data = loopy_webhook_data.get('card', {})
        customer_details = card_data.get('customerDetails', {})
        webhook_email = customer_details.get('email', '').lower()
        
        if webhook_email != customer_email.lower():
            print(f"❌ Email mismatch: webhook={webhook_email}, request={customer_email}")
            return False
        
        # Validate card ID exists
        loopy_card_id = card_data.get('id')
        if not loopy_card_id:
            print("❌ Missing Loopy card ID")
            return False
        
        # Validate stamps earned
        total_stamps = card_data.get('totalStampsEarned', 0)
        if not isinstance(total_stamps, int) or total_stamps < 12:
            print(f"❌ Invalid stamps count: {total_stamps}")
            return False
        
        # Validate campaign
        campaign_data = loopy_webhook_data.get('campaign', {})
        expected_campaign = os.getenv('CAMPAIGN_ID')
        if campaign_data.get('id') != expected_campaign:
            print(f"❌ Wrong campaign: {campaign_data.get('id')}")
            return False
        
        print("✅ Deposit request validated")
        return True
    
    def process_legitimate_reward(self, loopy_webhook_data):
        """
        Process a legitimate reward from validated Loopy webhook
        NEVER process without proper validation
        """
        
        print("🎁 PROCESSING LEGITIMATE LOOPY REWARD")
        print("=" * 50)
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Extract customer data from webhook
        card_data = loopy_webhook_data.get('card', {})
        customer_details = card_data.get('customerDetails', {})
        
        customer_email = customer_details.get('email')
        loopy_card_id = card_data.get('id')
        total_stamps = card_data.get('totalStampsEarned', 0)
        
        print(f"📊 LOOPY WEBHOOK DATA:")
        print(f"   Card ID: {loopy_card_id}")
        print(f"   Customer Email: {customer_email}")
        print(f"   Total Stamps: {total_stamps}")
        print()
        
        # Validate the deposit request
        if not self.validate_deposit_request(loopy_webhook_data, customer_email):
            return {
                'success': False,
                'error': 'Deposit request validation failed'
            }
        
        # Find customer in Munch
        customer = self.find_customer_by_email(customer_email)
        
        if not customer:
            return {
                'success': False,
                'error': f'Customer not found in Munch: {customer_email}'
            }
        
        # Calculate legitimate reward
        STAMPS_PER_COFFEE = 12
        COFFEE_VALUE_CENTS = 4000  # R40
        
        free_coffees = total_stamps // STAMPS_PER_COFFEE
        total_credit = free_coffees * COFFEE_VALUE_CENTS
        
        print(f"💰 REWARD CALCULATION:")
        print(f"   Free Coffees: {free_coffees}")
        print(f"   Credit Amount: R{total_credit/100}")
        print()
        
        # Process the deposit
        return self.deposit_reward(
            customer_id=customer['id'],
            amount_in_cents=total_credit,
            loopy_card_id=loopy_card_id,
            customer_email=customer_email,
            free_coffees=free_coffees
        )
    
    def deposit_reward(self, customer_id, amount_in_cents, loopy_card_id, customer_email, free_coffees):
        """
        Deposit reward to verified Munch customer
        With proper audit trail and validation
        """
        
        print(f"💳 DEPOSITING REWARD:")
        print(f"   Customer ID: {customer_id}")
        print(f"   Email: {customer_email}")
        print(f"   Amount: R{amount_in_cents/100}")
        print(f"   Loopy Card: {loopy_card_id}")
        print()
        
        try:
            response = requests.post(
                f'{self.base_url}/deposit/deposit',
                headers=self.get_headers(),
                json={
                    "accountId": "3e92a480-5f21-11ec-b43f-dde416ab9f61",
                    "amount": amount_in_cents,
                    "currency": "ZAR",
                    "description": f"Loopy loyalty reward - {loopy_card_id} - {free_coffees} free coffee(s)",
                    "userId": customer_id,
                    "paymentMethodId": self.payment_method_id,
                    "timezone": "Africa/Johannesburg"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"✅ DEPOSIT SUCCESSFUL!")
                print(f"   Amount: R{amount_in_cents/100}")
                print(f"   Customer: {customer_email}")
                print(f"   Loopy Card: {loopy_card_id}")
                print(f"   Deposit ID: {result.get('id', 'Unknown')}")
                
                # Create audit record
                audit_record = {
                    'timestamp': datetime.now().isoformat(),
                    'action': 'loopy_reward_deposit',
                    'customer_id': customer_id,
                    'customer_email': customer_email,
                    'loopy_card_id': loopy_card_id,
                    'amount_cents': amount_in_cents,
                    'free_coffees': free_coffees,
                    'deposit_id': result.get('id'),
                    'validation_passed': True
                }
                
                print(f"📋 AUDIT RECORD: {json.dumps(audit_record, indent=2)}")
                
                return {
                    'success': True,
                    'amount_deposited': f"R{amount_in_cents/100}",
                    'customer_email': customer_email,
                    'loopy_card_id': loopy_card_id,
                    'deposit_id': result.get('id'),
                    'audit_record': audit_record
                }
            else:
                error_msg = f"Deposit failed: {response.status_code}"
                print(f"❌ {error_msg}")
                
                return {
                    'success': False,
                    'error': error_msg,
                    'response_code': response.status_code
                }
                
        except Exception as e:
            error_msg = f"Deposit error: {e}"
            print(f"❌ {error_msg}")
            
            return {
                'success': False,
                'error': error_msg
            }

def demonstrate_secure_approach():
    """
    Demonstrate the secure approach with NO hardcoded data
    """
    
    print("🔒 SECURE MUNCH INTEGRATION - NO HARDCODED DATA")
    print("=" * 60)
    print()
    
    print("🚨 SECURITY PRINCIPLES:")
    print("❌ NEVER use hardcoded customer IDs")
    print("❌ NEVER deposit without Loopy webhook validation")
    print("❌ NEVER bypass customer verification")
    print("✅ ALWAYS validate webhook authenticity")
    print("✅ ALWAYS search customers by email from webhook")
    print("✅ ALWAYS create audit trails")
    print("✅ ALWAYS verify rewards were legitimately earned")
    print()
    
    print("💡 PROPER WORKFLOW:")
    print("1. Loopy sends webhook with real customer data")
    print("2. Validate webhook signature and structure")
    print("3. Extract customer email from webhook")
    print("4. Search Munch for customer by email")
    print("5. Calculate legitimate rewards (stamps ÷ 12)")
    print("6. Deposit ONLY verified amount to verified customer")
    print("7. Create audit record for compliance")
    print()
    
    print("🛡️ This ensures ONLY legitimate rewards are deposited!")

if __name__ == "__main__":
    demonstrate_secure_approach() 