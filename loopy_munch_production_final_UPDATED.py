#!/usr/bin/env python3
"""
Production Loopy-Munch Integration Service - UPDATED VERSION
============================================================

FIXES APPLIED:
1. ✅ Correct field mappings (Contact Number, Email address)  
2. ✅ Working Munch API endpoints (account/create-user, account/deposit)
3. ✅ Smart redemption logic to prevent double-redemptions
4. ✅ Proper phone number extraction
5. ✅ Real credit application that works

Complete integration with:
1. Real Loopy API for card lookup
2. Real Munch account creation and credit
3. Smart duplicate prevention
4. Webhook support
"""

import requests
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('production.env')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SmartRedemptionTracker:
    """Smart tracking that distinguishes between duplicate and new redemptions"""
    
    def __init__(self, db_path: str = "production_redemption_tracker.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for tracking redemptions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS redemptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                loyalty_code TEXT NOT NULL,
                customer_name TEXT,
                stamps_count INTEGER,
                total_rewards_earned INTEGER,
                rewards_redeemed_in_this_transaction INTEGER,
                munch_credit_amount REAL,
                munch_reference TEXT UNIQUE,
                munch_customer_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(loyalty_code, total_rewards_earned)
            )
        """)
        
        # Create indexes separately
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_loyalty_code ON redemptions(loyalty_code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_munch_reference ON redemptions(munch_reference)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON redemptions(created_at)")
        
        conn.commit()
        conn.close()
    
    def calculate_new_rewards_only(self, loyalty_code: str, total_rewards_earned: int) -> int:
        """Calculate how many NEW rewards this customer has that we haven't processed"""
        
        # Get the highest reward level we've already processed for this customer
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT MAX(total_rewards_earned) FROM redemptions 
            WHERE loyalty_code = ?
        """, (loyalty_code,))
        
        result = cursor.fetchone()
        conn.close()
        
        highest_processed = result[0] if result[0] is not None else 0
        
        # Only process NEW rewards beyond what we've already handled
        new_rewards = max(0, total_rewards_earned - highest_processed)
        
        logger.info(f"Customer {loyalty_code}: {total_rewards_earned} total rewards earned. "
                   f"Previously processed up to {highest_processed} rewards. New rewards: {new_rewards}")
        
        return new_rewards
    
    def record_redemption(self, loyalty_code: str, customer_name: str, 
                         stamps_count: int, total_rewards_earned: int,
                         rewards_redeemed_count: int, munch_credit_amount: float, 
                         munch_reference: str, munch_customer_id: str) -> bool:
        """Record a new redemption"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO redemptions 
                (loyalty_code, customer_name, stamps_count, total_rewards_earned,
                 rewards_redeemed_in_this_transaction, munch_credit_amount, 
                 munch_reference, munch_customer_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (loyalty_code, customer_name, stamps_count, total_rewards_earned,
                  rewards_redeemed_count, munch_credit_amount, munch_reference, munch_customer_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Recorded redemption: {loyalty_code} -> Level {total_rewards_earned} -> {munch_reference}")
            return True
            
        except sqlite3.IntegrityError as e:
            # This means we already processed this reward level for this customer
            logger.info(f"Already processed reward level {total_rewards_earned} for {loyalty_code}")
            return False
        except Exception as e:
            logger.error(f"Failed to record redemption: {e}")
            return False

class LoopyLoyaltyAPI:
    """Loopy Loyalty API client with CORRECT field mappings"""
    
    def __init__(self, api_key: str, api_secret: str, username: str, base_url: str = "https://api.loopyloyalty.com"):
        self.api_key = api_key
        self.api_secret = api_secret
        self.username = username
        self.base_url = base_url.rstrip('/')
        self.auth_token = None
        self.campaign_id = os.getenv('CAMPAIGN_ID', 'hZd5mudqN2NiIrq2XoM46')
        
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'X-API-Key': api_key,
            'User-Agent': 'MunchPOS-LoopyIntegration/1.0'
        })
    
    def authenticate(self) -> bool:
        """Authenticate with Loopy API"""
        try:
            auth_data = {
                "username": self.username,
                "password": self.api_secret
            }
            
            response = self.session.post(
                f"{self.base_url}/v1/account/login",
                json=auth_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.auth_token = result.get('token')
                
                # Update session headers - no Bearer prefix per documentation
                self.session.headers.update({
                    'Authorization': self.auth_token
                })
                
                logger.info(f"Successfully authenticated with Loopy API")
                return True
            else:
                logger.error(f"Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def get_customer_by_code(self, loyalty_code: str) -> Optional[Dict]:
        """Get customer information by loyalty code (PID)"""
        
        if not self.auth_token:
            if not self.authenticate():
                raise Exception("Failed to authenticate with Loopy API")
        
        try:
            # In Loopy, the loyalty code is the PID
            response = self.session.get(
                f"{self.base_url}/v1/card/{loyalty_code}?includeEvents=true",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully retrieved card data for {loyalty_code}")
                return data
            elif response.status_code == 403:
                logger.warning(f"Access denied for card {loyalty_code} - may belong to different account")
                return None
            elif response.status_code == 404:
                logger.warning(f"Card not found: {loyalty_code}")
                return None
            else:
                logger.error(f"Error getting card: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error in get_customer_by_code: {e}")
            return None
    
    def check_rewards_available(self, card_data: Dict) -> Dict:
        """Check how many rewards are available based on card data - FIXED FIELD MAPPINGS"""
        
        try:
            card = card_data.get('card', {})
            
            # Get stamp and reward information
            total_stamps = card.get('totalStampsEarned', 0)
            total_rewards_redeemed = card.get('totalRewardsRedeemed', 0)
            
            # ✅ CRITICAL FIX: Use actual totalRewardsEarned from Loopy API, not calculated from stamps!
            total_rewards_earned = card.get('totalRewardsEarned', 0)
            available_rewards = total_rewards_earned - total_rewards_redeemed
            
            # Get customer details
            customer_details = card.get('customerDetails', {})
            
            # Extract name - handle different field formats
            customer_name = (
                customer_details.get('Name') or 
                customer_details.get('name') or
                f"{customer_details.get('First Name', '')} {customer_details.get('Last Name', '')}".strip() or
                'Loopy Customer'
            )
            
            # ✅ FIXED: Use correct field names from Loopy API
            return {
                "available_rewards": max(0, available_rewards),
                "total_stamps": total_stamps,
                "total_rewards_earned": total_rewards_earned,
                "total_rewards_redeemed": total_rewards_redeemed,
                "stamps_needed_for_next": 12 - (total_stamps % 12),
                "customer_name": customer_name,
                "customer_email": customer_details.get('Email address', ''),  # ✅ FIXED: 'Email address' not 'email'
                "customer_phone": customer_details.get('Contact Number', ''),  # ✅ FIXED: 'Contact Number' not 'phone'
                "can_redeem": available_rewards > 0,
                "card_status": card.get('passStatus', 'unknown')
            }
            
        except Exception as e:
            logger.error(f"Error checking rewards: {e}")
            return {
                "available_rewards": 0, 
                "can_redeem": False,
                "total_stamps": 0,
                "total_rewards_earned": 0,
                "total_rewards_redeemed": 0,
                "customer_name": "Unknown",
                "customer_email": "",
                "customer_phone": "",
                "stamps_needed_for_next": 12,
                "card_status": "error"
            }

class WorkingMunchAPI:
    """Munch API client using the WORKING endpoints from WORKING_MUNCH_API_CONFIG.json"""
    
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
    
    def search_customer_by_phone(self, phone: str):
        """Search for existing customer by phone number"""
        try:
            # ✅ FIXED: Handle empty or None phone numbers
            if not phone or phone.strip() == '':
                logger.info("No phone number provided for customer search")
                return None
            
            # Get all users first
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
                users = result.get('data', {}).get('users', [])
                
                # Search for phone match
                phone_clean = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
                for user in users:
                    user_phone = user.get('phone', '')
                    if user_phone:  # ✅ Check if user_phone exists before cleaning
                        user_phone_clean = user_phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
                        if phone_clean in user_phone_clean or user_phone_clean in phone_clean:
                            logger.info(f"Found existing customer: {user.get('firstName')} {user.get('lastName')}")
                            return user
                
                logger.info(f"No existing customer found for phone {phone}")
                return None
            else:
                logger.warning(f"Failed to search customers: {response.status_code}")
                return None
                
        except Exception as e:
            logger.warning(f"Error searching customer: {e}")
            return None
    
    def create_customer_account(self, loyalty_code: str, customer_info: dict):
        """Create new customer account using WORKING endpoint"""
        
        try:
            customer_name = customer_info.get('customer_name', 'Loopy Customer')
            name_parts = customer_name.split(' ', 1)
            first_name = name_parts[0] if name_parts else 'Loopy'
            last_name = name_parts[1] if len(name_parts) > 1 else 'Customer'
            
            # ✅ FIXED: Use working create-user endpoint
            user_data = {
                "id": self.account_id,
                "firstName": first_name,
                "lastName": last_name,
                "email": customer_info.get('customer_email') or f"loopy_{loyalty_code}@customer.local",
                "phone": customer_info.get('customer_phone') or "+27000000000",  # Default phone if none provided
                "timezone": "Africa/Johannesburg"
            }
            
            logger.info(f"Creating customer: {first_name} {last_name}")
            
            response = self.session.post(
                f"{self.base_url}/account/create-user",
                json=user_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    customer = result.get('data', {}).get('user', {})
                    logger.info(f"Customer created successfully!")
                    return customer
                else:
                    logger.error(f"Failed to create customer: {result.get('message')}")
                    return None
            else:
                logger.error(f"Create customer HTTP error: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating customer: {e}")
            return None
    
    def apply_credit(self, customer_id: str, credit_amount: float, reference: str):
        """Apply credit to customer account using WORKING deposit endpoint"""
        
        try:
            # Convert to cents for API
            amount_cents = int(credit_amount * 100)
            
            # ✅ FIXED: Use working deposit endpoint with all required fields
            deposit_data = {
                "accountId": self.account_id,
                "userId": customer_id,
                "amount": amount_cents,
                "organisationId": self.organisation_id,
                "siteId": "4744ae7f-e951-4370-bfd3-a5e2221679cc",
                "companyId": "28c5e780-3707-11ec-88a8-dde416ab9f61",
                "employeeId": self.employee_id,
                "paymentMethodId": "0193bf43-bc83-744e-9510-bc20d2314fdb",
                "method": "manual",
                "displayName": "Loopy Loyalty Credit",
                "message": f"Free coffee credit from Loopy loyalty program - {reference}",
                "origin": "cloud.munch.portal"
            }
            
            logger.info(f"Applying R{credit_amount} credit...")
            
            response = self.session.post(
                f"{self.base_url}/account/deposit",
                json=deposit_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    deposit = result.get('data', {}).get('accountDeposit', {})
                    logger.info(f"Credit applied successfully!")
                    logger.info(f"Deposit ID: {deposit.get('id')}")
                    return deposit
                else:
                    logger.error(f"Failed to apply credit: {result.get('message')}")
                    return None
            else:
                logger.error(f"Apply credit HTTP error: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error applying credit: {e}")
            return None

class SmartProductionIntegration:
    """Production integration with smart duplicate prevention and working APIs"""
    
    def __init__(self, loopy_config: Dict):
        self.loopy = LoopyLoyaltyAPI(**loopy_config)
        self.munch = WorkingMunchAPI()
        self.tracker = SmartRedemptionTracker()
        
        # Authenticate with Loopy on initialization
        if self.loopy.authenticate():
            logger.info("✅ Loopy authentication successful!")
        else:
            logger.error("❌ Loopy authentication failed!")
    
    def process_loyalty_scan_smart(self, loyalty_code: str) -> Dict:
        """Process loyalty scan with smart duplicate prevention"""
        
        logger.info(f"Processing loyalty scan with smart logic: {loyalty_code}")
        
        try:
            # Step 1: Get customer data from Loopy
            card_data = self.loopy.get_customer_by_code(loyalty_code)
            
            if not card_data:
                return {
                    "success": False,
                    "error": "invalid_code",
                    "message": "Loyalty code not found or invalid"
                }
            
            # Step 2: Get current stamp/reward status
            reward_info = self.loopy.check_rewards_available(card_data)
            logger.info(f"Reward info keys: {list(reward_info.keys())}")
            logger.info(f"Reward info: {reward_info}")
            stamps_count = reward_info.get("total_stamps", 0)
            
            # Step 3: ✅ CORRECT LOGIC - Check if we've already credited these rewards
            # Available in Loopy = Rewards Earned - Rewards Redeemed  
            available_rewards = reward_info["available_rewards"]
            
            # Check if we've already processed this reward level
            new_rewards_count = self.tracker.calculate_new_rewards_only(loyalty_code, reward_info["total_rewards_earned"])
            
            logger.info(f"Customer {loyalty_code}: {reward_info['total_rewards_earned']} rewards earned, "
                       f"{reward_info['total_rewards_redeemed']} redeemed, "
                       f"{available_rewards} available, {new_rewards_count} new to process")
            
            if new_rewards_count == 0:
                # No new rewards OR already processed this level
                # Return success but no action - invisible to cashier
                return {
                    "success": True,
                    "has_redemption": False,
                    "message": "No new rewards to process",
                    "customer_name": reward_info.get("customer_name"),
                    "total_stamps": stamps_count,
                    "stamps_needed": reward_info.get("stamps_needed_for_next", 0),
                    "smart_logic": "✅ Duplicate prevention - already processed this reward level"
                }
            
            # Step 4: Process the NEW rewards only  
            logger.info(f"Processing {new_rewards_count} NEW rewards for {loyalty_code}")
            
            # Find or create Munch customer
            customer = None
            
            if reward_info.get("customer_phone"):
                customer = self.munch.search_customer_by_phone(reward_info["customer_phone"])
            
            if not customer:
                customer = self.munch.create_customer_account(loyalty_code, reward_info)
            
            if not customer:
                return {
                    "success": False,
                    "error": "customer_creation_failed",
                    "message": "Failed to create or find customer in Munch"
                }
            
            customer_id = customer.get('id')
            customer_name = f"{customer.get('firstName', '')} {customer.get('lastName', '')}".strip()
            
            # Use actual total rewards earned from Loopy API
            total_rewards_earned = reward_info["total_rewards_earned"]
            
            # Create unique reference
            credit_reference = f"LOOPY_{loyalty_code}_LVL{total_rewards_earned}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Step 5: Record redemption BEFORE applying credit
            credit_amount = new_rewards_count * 40.0  # R40 per NEW coffee
            
            recorded = self.tracker.record_redemption(
                loyalty_code=loyalty_code,
                customer_name=reward_info["customer_name"],
                stamps_count=stamps_count,
                total_rewards_earned=total_rewards_earned,
                rewards_redeemed_count=new_rewards_count,
                munch_credit_amount=credit_amount,
                munch_reference=credit_reference,
                munch_customer_id=customer_id
            )
            
            if not recorded:
                # This means we already processed this reward level
                # Return success but no action - invisible to cashier
                return {
                    "success": True,
                    "has_redemption": False,
                    "message": "Reward level already processed",
                    "customer_name": reward_info.get("customer_name"),
                    "total_stamps": stamps_count,
                    "smart_logic": "✅ Already processed this reward level"
                }
            
            # Step 6: Apply credit to Munch account
            credit_result = self.munch.apply_credit(customer_id, credit_amount, credit_reference)
            
            if not credit_result:
                return {
                    "success": False,
                    "error": "credit_application_failed",
                    "message": "Failed to apply credit to Munch account"
                }
            
            return {
                "success": True,
                "has_redemption": True,
                "loyalty_code": loyalty_code,
                "customer_name": reward_info["customer_name"],
                "customer_id": customer_id,
                "free_coffees": new_rewards_count,
                "credit_amount": credit_amount,
                "total_stamps": stamps_count,
                "total_rewards_earned": total_rewards_earned,
                "reference": credit_reference,
                "deposit_id": credit_result.get('id'),
                "cashier_message": f"✅ {new_rewards_count} FREE COFFEE(S) - R{credit_amount} CREDIT APPLIED",
                "cashier_instructions": [
                    f"1. Customer: {reward_info['customer_name']}",
                    f"2. Customer ID: {customer_id}",
                    f"3. NEW Credit Applied: R{credit_amount}",
                    f"4. Process coffee order and use account credit for payment",
                    f"5. Reference: {credit_reference}"
                ],
                "smart_logic": f"✅ Processed {new_rewards_count} NEW rewards (Level {total_rewards_earned})"
            }
            
        except Exception as e:
            logger.error(f"Error processing loyalty scan: {e}")
            return {
                "success": False,
                "error": "processing_error",
                "message": f"Failed to process loyalty code: {str(e)}"
            }

# Flask application
app = Flask(__name__)
CORS(app)

# Load configuration
def load_configuration():
    """Load configuration from environment variables"""
    
    loopy_config = {
        "api_key": os.getenv('LOOPY_API_KEY'),
        "api_secret": os.getenv('LOOPY_API_SECRET'), 
        "username": os.getenv('LOOPY_USERNAME'),
        "base_url": os.getenv('LOOPY_BASE_URL', 'https://api.loopyloyalty.com')
    }
    
    return loopy_config

# Initialize service
loopy_config = load_configuration()

if all(loopy_config.values()):
    integration_service = SmartProductionIntegration(loopy_config)
    logger.info("✅ Smart production integration service initialized successfully")
else:
    integration_service = None
    logger.error("❌ Failed to initialize integration service - check configuration")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    
    health_status = {
        "status": "healthy" if integration_service else "unhealthy",
        "service": "smart_loopy_munch_integration",
        "timestamp": datetime.now().isoformat(),
        "version": "4.0.0",
        "features": [
            "✅ Smart duplicate prevention",
            "✅ Working Munch API endpoints", 
            "✅ Correct field mappings",
            "✅ Real credit application",
            "✅ Persistent tracking database"
        ],
        "configuration": {
            "loopy_configured": bool(integration_service and integration_service.loopy),
            "munch_configured": bool(integration_service and integration_service.munch),
            "tracker_configured": bool(integration_service and integration_service.tracker),
            "loopy_authenticated": bool(integration_service and integration_service.loopy.auth_token) if integration_service else False
        },
        "mode": "production"
    }
    
    return jsonify(health_status)

@app.route('/scan', methods=['POST'])
def process_scan():
    """Process loyalty code scan with smart logic"""
    
    if not integration_service:
        return jsonify({
            "success": False,
            "error": "service_unavailable",
            "message": "Integration service not properly configured"
        }), 503
    
    try:
        data = request.get_json()
        if not data or not data.get("loyalty_code"):
            return jsonify({
                "success": False,
                "error": "missing_loyalty_code", 
                "message": "loyalty_code is required"
            }), 400
        
        loyalty_code = data["loyalty_code"].strip()
        
        # ✅ Use smart processing with duplicate prevention
        result = integration_service.process_loyalty_scan_smart(loyalty_code)
        result["processed_at"] = datetime.now().isoformat()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in scan endpoint: {e}")
        return jsonify({
            "success": False,
            "error": "server_error",
            "message": "Internal server error"
        }), 500

@app.route('/webhook/loopy/enrolled', methods=['POST'])
def loopy_enrollment_webhook():
    """Handle Loopy enrollment webhooks from Make.com with smart processing"""
    
    logger.info("=" * 60)
    logger.info("WEBHOOK DEBUG")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Raw Data: {request.get_data(as_text=True)}")
    logger.info("=" * 60)
    
    if not integration_service:
        return jsonify({"error": "Service not configured"}), 503
    
    try:
        # Extract PID from webhook data
        pid = None
        
        # Check URL parameters first
        pid = request.args.get('pid') or request.args.get('cardId') or request.args.get('loyalty_code')
        
        # Check form data
        if not pid:
            pid = request.form.get('pid') or request.form.get('cardId') or request.form.get('loyalty_code')
        
        # Check JSON
        if not pid:
            try:
                data = request.get_json()
                if data and isinstance(data, dict):
                    pid = data.get('pid') or data.get('cardId') or data.get('loyalty_code')
                    if not pid and 'card' in data:
                        card = data.get('card', {})
                        if isinstance(card, dict):
                            pid = card.get('id') or card.get('pid')
            except Exception as e:
                logger.warning(f"JSON parsing failed: {e}")
        
        # Extract from raw text if needed
        if not pid:
            try:
                raw_text = request.get_data(as_text=True)
                import re
                pid_patterns = re.findall(r'[A-Za-z0-9]{10,20}', raw_text)
                if pid_patterns:
                    pid = pid_patterns[0]
            except Exception as e:
                logger.warning(f"Pattern matching failed: {e}")
        
        logger.info(f"🎯 Final extracted PID: {pid}")
        
        if not pid:
            logger.error("❌ NO PID FOUND - Make.com configuration issue!")
            return jsonify({
                "error": "No PID found in webhook",
                "raw_data": request.get_data(as_text=True),
                "help": "Check Make.com HTTP module body configuration"
            }), 400
        
        logger.info(f"🚀 Processing webhook for PID: {pid}")
        
        # ✅ Process with smart logic
        result = integration_service.process_loyalty_scan_smart(pid)
        
        return jsonify({
            "webhook_processed": True,
            "pid": pid,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({
            "error": "Webhook processing failed",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('SERVICE_PORT', '5004'))
    
    print("🚀 SMART LOOPY-MUNCH INTEGRATION SERVICE v4.0")
    print("=" * 60)
    print("✅ ALL FIXES APPLIED:")
    print("  • ✅ Smart duplicate prevention")
    print("  • ✅ Working Munch API endpoints")
    print("  • ✅ Correct field mappings (Contact Number, Email address)")
    print("  • ✅ Real credit application")
    print("  • ✅ Persistent tracking database")
    print()
    print(f"🌐 Service URL: http://localhost:{port}")
    print(f"💚 Health Check: GET http://localhost:{port}/health")
    print(f"📱 Scan Endpoint: POST http://localhost:{port}/scan")
    print(f"🔗 Webhook: POST http://localhost:{port}/webhook/loopy/enrolled")
    print()
    print("🎯 Smart Features:")
    print("  • No duplicate R40 credits for same reward level")
    print("  • Invisible duplicate prevention (no cashier errors)")
    print("  • Customer can hold credits while earning more stamps")
    print("  • Automatic progression to next reward level")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=False) 