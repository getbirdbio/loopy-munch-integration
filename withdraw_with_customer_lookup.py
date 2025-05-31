#!/usr/bin/env python3
"""
Withdraw Excess Credits with Customer ID Lookup
==============================================
1. Load excess credit data from previous calculation
2. Look up customer IDs from Munch API by name
3. Withdraw excess credits from customer accounts
"""

import json
import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MunchAPIWithLookup:
    """Munch API client with customer lookup and withdrawal capabilities"""
    
    def __init__(self):
        # Load working configuration
        with open('WORKING_MUNCH_API_CONFIG.json', 'r') as f:
            config = json.load(f)
        
        with open('munch_tokens.json', 'r') as f:
            tokens = json.load(f)
        
        self.base_url = config["munch_api"]["base_url"]
        self.account_id = config["munch_api"]["account_id"]
        self.organisation_id = config["munch_api"]["organisation_id"]
        self.employee_id = config["munch_api"]["employee_id"]
        self.bearer_token = tokens["bearer_token"]
        
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.bearer_token}",
            "Authorization-Type": "internal",
            "Content-Type": "application/json",
            "Locale": "en",
            "Munch-Platform": "cloud.munch.portal",
            "Munch-Timezone": "Africa/Johannesburg",
            "Munch-Version": "2.20.1",
            "Munch-Employee": self.employee_id,
            "Munch-Organisation": self.organisation_id
        })
        
        # Cache all users for faster lookups
        self.all_users = None
        self.load_all_users()
    
    def load_all_users(self):
        """Load all users once for faster lookups"""
        try:
            users_data = {
                "id": self.account_id,
                "timezone": "Africa/Johannesburg"
            }
            
            response = self.session.post(
                f"{self.base_url}/account/retrieve-users",
                json=users_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                self.all_users = result.get('data', {}).get('users', [])
                logger.info(f"✅ Loaded {len(self.all_users)} users for lookup")
            else:
                logger.error(f"Failed to load users: {response.status_code}")
                self.all_users = []
                
        except Exception as e:
            logger.error(f"Error loading users: {e}")
            self.all_users = []
    
    def find_customer_by_name(self, customer_name: str) -> Optional[Dict]:
        """Find customer by name from cached users"""
        
        if not self.all_users:
            logger.warning("No users loaded for lookup")
            return None
        
        # Clean the search name
        search_name = customer_name.lower().strip()
        
        # Try exact matches first
        for user in self.all_users:
            first_name = user.get('firstName', '').lower()
            last_name = user.get('lastName', '').lower()
            full_name = f"{first_name} {last_name}".strip()
            
            if search_name == full_name or search_name == first_name:
                logger.info(f"✅ Found exact match: {user.get('firstName')} {user.get('lastName')}")
                return user
        
        # Try partial matches
        for user in self.all_users:
            first_name = user.get('firstName', '').lower()
            last_name = user.get('lastName', '').lower()
            full_name = f"{first_name} {last_name}".strip()
            
            if (search_name in full_name or 
                any(part in first_name for part in search_name.split()) or
                any(part in last_name for part in search_name.split())):
                logger.info(f"✅ Found partial match: {user.get('firstName')} {user.get('lastName')}")
                return user
        
        logger.warning(f"❌ No customer found for: {customer_name}")
        return None
    
    def get_customer_balance(self, customer_id: str) -> float:
        """Get customer's current account balance with fresh data"""
        
        try:
            # Try to refresh all users data to get latest balances
            logger.info(f"Refreshing user data to get current balance for {customer_id}")
            self.load_all_users()
            
            # Now get from refreshed cache
            for user in self.all_users or []:
                if user.get('id') == customer_id:
                    # Check if balance is in accounts array
                    accounts = user.get('accounts', [])
                    if accounts:
                        for account in accounts:
                            if account.get('id') == self.account_id:
                                account_user = account.get('accountUser', {})
                                balance_cents = account_user.get('balance', 0)
                                credit_balance_cents = account_user.get('creditBalance', 0) 
                                total_balance_cents = balance_cents + credit_balance_cents
                                logger.info(f"Fresh balance for {customer_id}: {balance_cents} cents balance + {credit_balance_cents} cents credit = {total_balance_cents} cents = R{total_balance_cents/100:.2f}")
                                return total_balance_cents / 100.0  # Convert from cents
                    
                    # Fallback to old method
                    account_user = user.get('accountUser', {})
                    if account_user:
                        balance_cents = account_user.get('balance', 0)
                        logger.info(f"Fallback balance for {customer_id}: {balance_cents} cents = R{balance_cents/100:.2f}")
                        return balance_cents / 100.0
                    
            logger.warning(f"Customer {customer_id} not found in refreshed user list")
            return 0.0
                
        except Exception as e:
            logger.error(f"Error getting balance for {customer_id}: {e}")
            return 0.0
    
    def withdraw_credit(self, customer_id: str, withdraw_amount: float, reference: str):
        """Withdraw excess credit from customer account"""
        
        try:
            # Convert to cents for API (positive amount for withdrawal)
            amount_cents = int(withdraw_amount * 100)
            
            # Use withdraw endpoint
            withdraw_data = {
                "accountId": self.account_id,
                "userId": customer_id,
                "amount": amount_cents,  # Positive amount for withdrawal
                "organisationId": self.organisation_id,
                "siteId": "4744ae7f-e951-4370-bfd3-a5e2221679cc",
                "companyId": "28c5e780-3707-11ec-88a8-dde416ab9f61",
                "employeeId": self.employee_id,
                "paymentMethodId": "0193bf43-bc83-744e-9510-bc20d2314fdb",
                "method": "manual",
                "displayName": "Loopy Credit Correction",
                "message": f"Withdrawal of excess credit due to calculation bug - {reference}",
                "origin": "cloud.munch.portal"
            }
            
            logger.info(f"Withdrawing R{withdraw_amount} excess credit...")
            
            response = self.session.post(
                f"{self.base_url}/account/withdraw",
                json=withdraw_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    withdrawal = result.get('data', {}).get('accountWithdrawal', {})
                    logger.info(f"✅ Withdrawal successful!")
                    logger.info(f"📄 Withdrawal ID: {withdrawal.get('id')}")
                    return withdrawal
                else:
                    logger.error(f"❌ Failed to withdraw: {result.get('message')}")
                    return None
            else:
                logger.error(f"❌ Withdraw HTTP error: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error withdrawing credit: {e}")
            return None

def load_excess_credit_data():
    """Load excess credit data from previous calculation"""
    
    print("🔍 LOADING EXCESS CREDIT DATA")
    print("=" * 60)
    
    # Load the previous excess credit calculation
    excess_file = "excess_credit_withdrawals_20250531_093420.json"
    
    try:
        with open(excess_file, 'r') as f:
            excess_data = json.load(f)
    except FileNotFoundError:
        logger.error(f"Excess credit file not found: {excess_file}")
        return []
    
    # Get customers with failed withdrawals (they need customer ID lookup)
    failed_withdrawals = [r for r in excess_data.get('results', []) if r.get('status') == 'failed' and r.get('excess_amount', 0) > 0]
    
    print(f"📊 Found {len(failed_withdrawals)} customers with excess credits")
    total_excess = sum(r.get('excess_amount', 0) for r in failed_withdrawals)
    print(f"💰 Total excess to withdraw: R{total_excess:,.2f}")
    print()
    
    return failed_withdrawals

def lookup_customers_and_withdraw():
    """Look up customer IDs and withdraw excess credits"""
    
    # Load excess credit data
    failed_withdrawals = load_excess_credit_data()
    
    if not failed_withdrawals:
        print("✅ No excess credits to withdraw!")
        return
    
    print("🔍 LOOKING UP CUSTOMER IDs AND CHECKING BALANCES")
    print("=" * 60)
    
    # Initialize Munch API
    munch = MunchAPIWithLookup()
    
    withdrawals_needed = []
    customers_found = 0
    customers_not_found = 0
    insufficient_balance = 0
    
    for i, withdrawal_data in enumerate(failed_withdrawals, 1):
        customer_code = withdrawal_data.get('customer_code')
        customer_name = withdrawal_data.get('customer_name', 'Unknown')
        excess_amount = withdrawal_data.get('excess_amount', 0)
        
        print(f"[{i:3d}/{len(failed_withdrawals)}] {customer_code} - {customer_name[:25]:25s}")
        print(f"   🔄 Excess: R{excess_amount:6.2f}")
        
        # Look up customer in Munch
        customer = munch.find_customer_by_name(customer_name)
        
        if customer:
            customer_id = customer.get('id')
            current_balance = munch.get_customer_balance(customer_id)
            customers_found += 1
            
            print(f"   👤 Found: {customer.get('firstName')} {customer.get('lastName')}")
            print(f"   💳 Balance: R{current_balance:.2f}")
            
            # Add to withdrawal list regardless of current balance (accounting correction)
            print(f"   ✅ Ready for accounting correction withdrawal")
            
            withdrawals_needed.append({
                **withdrawal_data,
                'customer_id': customer_id,
                'current_balance': current_balance
            })
            
            if current_balance < excess_amount:
                insufficient_balance += 1
                print(f"   ⚠️  Will create negative balance (need R{excess_amount:.2f}, have R{current_balance:.2f})")
        else:
            customers_not_found += 1
            print(f"   ❌ Customer not found in Munch")
        
        print()
        
        # Rate limiting
        if i % 10 == 0:
            time.sleep(1)
    
    print("📊 CUSTOMER LOOKUP SUMMARY")
    print("=" * 60)
    print(f"👤 Customers found in Munch: {customers_found}")
    print(f"❌ Customers not found: {customers_not_found}")
    print(f"⚠️  Will create negative balances: {insufficient_balance}")
    print(f"💸 Ready for accounting correction: {len(withdrawals_needed)}")
    
    if withdrawals_needed:
        total_ready = sum(w['excess_amount'] for w in withdrawals_needed)
        print(f"💰 Total excess to withdraw: R{total_ready:,.2f}")
        print(f"📊 Average per customer: R{total_ready/len(withdrawals_needed):.2f}")
        print()
        print("⚠️  NOTE: Most customers have R0.00 balance - withdrawals will create negative balances")
        print("   This is correct for accounting purposes to remove excess credits.")
    
    return withdrawals_needed

def withdraw_excess_credits(withdrawals_needed: List[Dict]):
    """Withdraw excess credits from customers"""
    
    if not withdrawals_needed:
        print("✅ No excess credits ready for withdrawal!")
        return
    
    print(f"\n🚀 ACCOUNTING CORRECTION: WITHDRAWING EXCESS CREDITS FROM {len(withdrawals_needed)} CUSTOMERS")
    print("=" * 60)
    
    # Confirm with user
    total_to_withdraw = sum(w['excess_amount'] for w in withdrawals_needed)
    print(f"⚠️  ABOUT TO WITHDRAW R{total_to_withdraw:,.2f} FROM {len(withdrawals_needed)} CUSTOMERS")
    print(f"⚠️  This will likely create NEGATIVE BALANCES to correct the accounting error")
    print()
    
    confirm = input("Type 'WITHDRAW' to confirm this action: ").strip()
    if confirm != 'WITHDRAW':
        print("❌ Withdrawal cancelled")
        return
    
    # Initialize Munch API
    munch = MunchAPIWithLookup()
    
    results = []
    successful_withdrawals = 0
    total_withdrawn = 0
    
    for i, withdrawal in enumerate(withdrawals_needed, 1):
        customer_code = withdrawal['customer_code']
        customer_name = withdrawal['customer_name']
        customer_id = withdrawal['customer_id']
        excess_amount = withdrawal['excess_amount']
        
        print(f"[{i:3d}/{len(withdrawals_needed)}] Processing {customer_code} - {customer_name}")
        print(f"   💰 Withdrawing R{excess_amount:.2f} from {customer_id}")
        
        # Create reference
        withdraw_reference = f"EXCESS_WITHDRAWAL_{customer_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Withdraw excess credit
        withdraw_result = munch.withdraw_credit(customer_id, excess_amount, withdraw_reference)
        
        if withdraw_result:
            print(f"   ✅ Withdrew R{excess_amount:.2f}")
            print(f"   🎯 Reference: {withdraw_reference}")
            print(f"   📄 Withdrawal ID: {withdraw_result.get('id')}")
            
            successful_withdrawals += 1
            total_withdrawn += excess_amount
            
            results.append({
                **withdrawal,
                'status': 'success',
                'withdrawal_id': withdraw_result.get('id'),
                'withdraw_reference': withdraw_reference
            })
        else:
            print(f"   ❌ Failed to withdraw")
            results.append({**withdrawal, 'status': 'failed', 'error': 'API call failed'})
        
        print()
        
        # Rate limiting
        time.sleep(0.5)
    
    # Save results
    results_data = {
        'timestamp': datetime.now().isoformat(),
        'total_customers': len(withdrawals_needed),
        'successful_withdrawals': successful_withdrawals,
        'total_withdrawn': total_withdrawn,
        'results': results
    }
    
    results_filename = f"successful_withdrawals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_filename, 'w') as f:
        json.dump(results_data, f, indent=2)
    
    print("📊 WITHDRAWAL COMPLETE!")
    print("=" * 60)
    print(f"✅ Successful withdrawals: {successful_withdrawals}/{len(withdrawals_needed)}")
    print(f"💸 Total withdrawn: R{total_withdrawn:,.2f}")
    print(f"📁 Results saved to: {results_filename}")
    
    if successful_withdrawals < len(withdrawals_needed):
        failed = len(withdrawals_needed) - successful_withdrawals
        print(f"⚠️  {failed} withdrawals failed - check results file for details")

def main():
    """Main function"""
    
    print("🔧 LOOPY-MUNCH EXCESS CREDIT WITHDRAWAL TOOL v3.0")
    print("=" * 60)
    print("This tool will:")
    print("1. Load excess credit data from previous calculation")
    print("2. Look up customer IDs in Munch by name")
    print("3. Check customer balances")
    print("4. Withdraw excess credits")
    print()
    
    # Step 1: Look up customers and prepare withdrawals
    withdrawals_needed = lookup_customers_and_withdraw()
    
    if not withdrawals_needed:
        print("✅ No customers ready for withdrawal!")
        return
    
    # Step 2: Withdraw excess credits
    withdraw_excess_credits(withdrawals_needed)

if __name__ == "__main__":
    main() 