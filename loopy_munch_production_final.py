#!/usr/bin/env python3
"""
Production Loopy-Munch Integration Service - Final Version
==========================================================

Complete integration with:
1. Real Loopy API for card lookup
2. Real Munch account creation and credit
3. Webhook support
"""

import requests
import json
import logging
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

class LoopyLoyaltyAPI:
    """Loopy Loyalty API client with official endpoints"""
    
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
        """Check how many rewards are available based on card data"""
        
        try:
            card = card_data.get('card', {})
            
            # Get stamp information
            total_stamps = card.get('totalStampsEarned', 0)
            total_rewards_redeemed = card.get('totalRewardsRedeemed', 0)
            
            # Calculate available rewards (12 stamps = 1 coffee)
            stamps_per_reward = int(os.getenv('STAMPS_FOR_FREE_COFFEE', 12))
            total_rewards_earned = total_stamps // stamps_per_reward
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
            
            return {
                "available_rewards": max(0, available_rewards),
                "total_stamps": total_stamps,
                "total_rewards_earned": total_rewards_earned,
                "total_rewards_redeemed": total_rewards_redeemed,
                "stamps_needed_for_next": stamps_per_reward - (total_stamps % stamps_per_reward),
                "customer_name": customer_name,
                "customer_email": customer_details.get('email', ''),
                "customer_phone": customer_details.get('phone', ''),
                "can_redeem": available_rewards > 0,
                "card_status": card.get('passStatus', 'unknown')
            }
            
        except Exception as e:
            logger.error(f"Error checking rewards: {e}")
            return {"available_rewards": 0, "can_redeem": False}

class MunchAccountManager:
    """Real Munch POS account management"""
    
    def __init__(self, base_url: str, api_key: str, organization_id: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.organization_id = organization_id
        self.coffee_price = float(os.getenv('COFFEE_PRICE', 40.00))
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'{api_key}',
            'Content-Type': 'application/json'
        })
    
    def search_customer_by_phone(self, phone: str) -> Optional[Dict]:
        """Search for existing customer by phone number"""
        
        try:
            # Clean phone number
            phone_clean = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            
            response = self.session.get(
                f"{self.base_url}/members/search",
                params={'q': phone_clean},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    return data[0]  # Return first match
            
        except Exception as e:
            logger.warning(f"Error searching customer by phone: {e}")
        
        return None
    
    def create_customer_account(self, loyalty_code: str, customer_info: Dict) -> Dict:
        """Create new customer account in Munch"""
        
        try:
            # Clean and format customer data
            customer_name = customer_info.get('customer_name', 'Loopy Customer')
            name_parts = customer_name.split(' ', 1)
            first_name = name_parts[0] if name_parts else 'Loopy'
            last_name = name_parts[1] if len(name_parts) > 1 else 'Customer'
            
            # Create unique account code
            account_code = f"LOOPY{loyalty_code[-6:].upper()}"
            
            member_data = {
                "memberNumber": account_code,
                "firstName": first_name,
                "lastName": last_name,
                "email": customer_info.get('customer_email') or f"{account_code.lower()}@customer.local",
                "cellNumber": customer_info.get('customer_phone', ''),
                "birthDate": None,
                "customerId": None,
                "externalId": f"loopy_{loyalty_code}",
                "isActive": True,
                "metadata": {
                    "loopy_loyalty_code": loyalty_code,
                    "source": "loopy_integration",
                    "created": datetime.now().isoformat(),
                    "total_stamps": customer_info.get('total_stamps', 0)
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/members",
                json=member_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                member = response.json()
                logger.info(f"Created new Munch member: {member.get('memberNumber')}")
                return member
            else:
                logger.error(f"Failed to create member: {response.status_code} - {response.text}")
                raise Exception(f"Failed to create Munch account: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error creating customer account: {e}")
            raise
    
    def add_coffee_credit(self, member_id: str, num_coffees: int = 1, reference: str = None) -> Dict:
        """Add coffee credit to customer account"""
        
        credit_amount = num_coffees * self.coffee_price
        
        try:
            # Create transaction for deposit
            transaction_data = {
                "memberId": member_id,
                "amount": credit_amount,
                "paymentMethodId": "loyalty_reward",
                "origin": "LOYALTY_REWARD",
                "type": "deposit",
                "reference": reference or f"LOOPY_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "description": f"Loopy loyalty redemption - {num_coffees} free coffee(s)",
                "metadata": {
                    "source": "loopy_integration",
                    "num_coffees": num_coffees,
                    "created": datetime.now().isoformat()
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/member-transactions",
                json=transaction_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                transaction = response.json()
                logger.info(f"Added R{credit_amount} credit for member {member_id}")
                return transaction
            else:
                logger.error(f"Failed to add credit: {response.status_code} - {response.text}")
                raise Exception(f"Failed to add credit: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error adding coffee credit: {e}")
            raise

class ProductionLoopyMunchIntegration:
    """Production-ready integration service"""
    
    def __init__(self, loopy_config: Dict, munch_config: Dict):
        self.loopy = LoopyLoyaltyAPI(**loopy_config)
        self.munch = MunchAccountManager(**munch_config)
        self.processed_codes = {}
        
        # Authenticate with Loopy on initialization
        if self.loopy.authenticate():
            logger.info("✅ Loopy authentication successful!")
        else:
            logger.error("❌ Loopy authentication failed!")
    
    def process_loyalty_scan(self, loyalty_code: str) -> Dict:
        """Process loyalty code scan - complete flow"""
        
        logger.info(f"Processing loyalty scan: {loyalty_code}")
        
        try:
            # Check if already processed recently
            if loyalty_code in self.processed_codes:
                last_processed = self.processed_codes[loyalty_code]
                time_diff = (datetime.now() - last_processed).seconds
                if time_diff < 300:  # 5 minutes
                    return {
                        "success": False,
                        "error": "recently_processed",
                        "message": f"This code was processed {time_diff} seconds ago",
                        "wait_seconds": 300 - time_diff
                    }
            
            # Step 1: Get customer data from Loopy
            card_data = self.loopy.get_customer_by_code(loyalty_code)
            
            if not card_data:
                return {
                    "success": False,
                    "error": "invalid_code",
                    "message": "Loyalty code not found or invalid"
                }
            
            # Step 2: Check available rewards
            reward_info = self.loopy.check_rewards_available(card_data)
            
            if not reward_info["can_redeem"]:
                return {
                    "success": True,
                    "has_redemption": False,
                    "message": "No free coffees available yet",
                    "customer_name": reward_info.get("customer_name"),
                    "total_stamps": reward_info.get("total_stamps", 0),
                    "stamps_needed": reward_info.get("stamps_needed_for_next", 0),
                    "total_rewards_earned": reward_info.get("total_rewards_earned", 0),
                    "total_rewards_redeemed": reward_info.get("total_rewards_redeemed", 0)
                }
            
            available_rewards = reward_info["available_rewards"]
            
            # Step 3: Find or create Munch customer
            member = None
            
            # First try to find by phone if available
            if reward_info.get("customer_phone"):
                member = self.munch.search_customer_by_phone(reward_info["customer_phone"])
            
            # If not found, create new account
            if not member:
                member = self.munch.create_customer_account(loyalty_code, reward_info)
            
            member_id = member.get('id')
            member_number = member.get('memberNumber')
            
            # Step 4: Add coffee credit to Munch account
            credit_reference = f"LOOPY_{loyalty_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            credit_result = self.munch.add_coffee_credit(
                member_id, 
                available_rewards, 
                credit_reference
            )
            
            # Track as processed
            self.processed_codes[loyalty_code] = datetime.now()
            
            credit_amount = available_rewards * self.munch.coffee_price
            
            return {
                "success": True,
                "has_redemption": True,
                "loyalty_code": loyalty_code,
                "customer_name": reward_info["customer_name"],
                "member_number": member_number,
                "member_id": member_id,
                "free_coffees": available_rewards,
                "credit_amount": credit_amount,
                "total_stamps": reward_info["total_stamps"],
                "reference": credit_reference,
                "transaction_id": credit_result.get('id'),
                "cashier_message": f"✅ {available_rewards} FREE COFFEE(S) - R{credit_amount} CREDIT APPLIED",
                "cashier_instructions": [
                    f"1. Customer: {reward_info['customer_name']}",
                    f"2. Member Number: {member_number}",
                    f"3. Credit Applied: R{credit_amount}",
                    f"4. Process coffee order and use member account for payment"
                ]
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
    """Load configuration from environment variables and config files"""
    
    loopy_config = {
        "api_key": os.getenv('LOOPY_API_KEY'),
        "api_secret": os.getenv('LOOPY_API_SECRET'), 
        "username": os.getenv('LOOPY_USERNAME'),
        "base_url": os.getenv('LOOPY_BASE_URL', 'https://api.loopyloyalty.com')
    }
    
    try:
        with open('munch_tokens.json', 'r') as f:
            tokens = json.load(f)
        
        munch_config = {
            "base_url": os.getenv('MUNCH_BASE_URL', 'https://api.munch.cloud/api'),
            "api_key": tokens["bearer_token"],
            "organization_id": tokens["organisation_id"]
        }
    except Exception as e:
        logger.error(f"Failed to load Munch configuration: {e}")
        munch_config = {
            "base_url": os.getenv('MUNCH_BASE_URL', 'https://api.munch.cloud/api'),
            "api_key": os.getenv('MUNCH_API_KEY'),
            "organization_id": os.getenv('MUNCH_ORGANIZATION_ID')
        }
    
    return loopy_config, munch_config

# Initialize service
loopy_config, munch_config = load_configuration()

if munch_config and all(loopy_config.values()):
    integration_service = ProductionLoopyMunchIntegration(loopy_config, munch_config)
    logger.info("Production integration service initialized successfully")
else:
    integration_service = None
    logger.error("Failed to initialize integration service - check configuration")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    
    health_status = {
        "status": "healthy" if integration_service else "unhealthy",
        "service": "production_loopy_munch_integration",
        "timestamp": datetime.now().isoformat(),
        "version": "3.0.0",
        "configuration": {
            "loopy_configured": bool(integration_service and integration_service.loopy),
            "munch_configured": bool(integration_service and integration_service.munch),
            "loopy_authenticated": bool(integration_service and integration_service.loopy.auth_token) if integration_service else False
        },
        "mode": "production"
    }
    
    return jsonify(health_status)

@app.route('/scan', methods=['POST'])
def process_scan():
    """Process loyalty code scan"""
    
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
        
        result = integration_service.process_loyalty_scan(loyalty_code)
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
    """Handle Loopy enrollment webhooks from Make.com"""
    
    # Debug logging
    logger.info("=" * 60)
    logger.info("WEBHOOK DEBUG")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Content-Type: {request.content_type}")
    logger.info(f"Raw Data: {request.data}")
    logger.info(f"Get Data as Text: {request.get_data(as_text=True)}")
    logger.info(f"Content Length: {request.content_length}")
    logger.info(f"Args: {dict(request.args)}")
    logger.info(f"Form: {dict(request.form)}")
    logger.info("=" * 60)
    
    if not integration_service:
        return jsonify({"error": "Service not configured"}), 503
    
    try:
        # Try multiple methods to extract PID from Make.com data
        pid = None
        data = None
        
        # Method 1: Check URL parameters first
        pid = request.args.get('pid') or request.args.get('cardId') or request.args.get('loyalty_code')
        if pid:
            logger.info(f"✅ PID found in URL parameters: {pid}")
        
        # Method 2: Check form data
        if not pid:
            pid = request.form.get('pid') or request.form.get('cardId') or request.form.get('loyalty_code')
            if pid:
                logger.info(f"✅ PID found in form data: {pid}")
        
        # Method 3: Standard JSON parsing
        if not pid:
            try:
                data = request.get_json()
                if data and isinstance(data, dict):
                    pid = data.get('pid') or data.get('cardId') or data.get('loyalty_code')
                    # Check nested card object
                    if not pid and 'card' in data:
                        card = data.get('card', {})
                        if isinstance(card, dict):
                            pid = card.get('id') or card.get('pid')
                    if pid:
                        logger.info(f"✅ PID found in JSON: {pid}")
            except Exception as e:
                logger.warning(f"Standard JSON parsing failed: {e}")
        
        # Method 4: Force JSON parsing (for malformed JSON)
        if not pid:
            try:
                raw_text = request.get_data(as_text=True)
                logger.info(f"Attempting to extract PID from raw text: {raw_text}")
                
                # Try to find PID-like strings in the raw data
                import re
                # Look for alphanumeric strings that could be PIDs (10-20 chars)
                pid_patterns = re.findall(r'[A-Za-z0-9]{10,20}', raw_text)
                if pid_patterns:
                    pid = pid_patterns[0]  # Take the first match
                    logger.info(f"✅ PID extracted from pattern matching: {pid}")
                    
            except Exception as e:
                logger.warning(f"Pattern matching failed: {e}")
        
        # Method 5: Simple text extraction (for when Make.com sends just the PID)
        if not pid:
            try:
                raw_text = request.get_data(as_text=True).strip()
                # Remove quotes and check if it's a reasonable PID
                cleaned = raw_text.replace('"', '').replace("'", '').strip()
                if 8 <= len(cleaned) <= 25 and cleaned.replace('_', '').replace('-', '').isalnum():
                    pid = cleaned
                    logger.info(f"✅ PID extracted from simple text: {pid}")
            except Exception as e:
                logger.warning(f"Simple text extraction failed: {e}")
        
        logger.info(f"🎯 Final extracted PID: {pid}")
        
        if not pid:
            logger.error("❌ NO PID FOUND - Make.com configuration issue!")
            return jsonify({
                "error": "No PID found in webhook",
                "raw_data": request.get_data(as_text=True),
                "headers": dict(request.headers),
                "args": dict(request.args),
                "form": dict(request.form),
                "help": "Check Make.com HTTP module body configuration",
                "suggested_body": '{"pid": "{{1.Bundle.value.pid}}"}'
            }), 400
        
        logger.info(f"🚀 Processing webhook for PID: {pid}")
        
        # Process if customer has enough stamps
        result = integration_service.process_loyalty_scan(pid)
        
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
            "details": str(e),
            "raw_data": request.get_data(as_text=True)
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('SERVICE_PORT', '5004'))
    
    print("🚀 PRODUCTION LOOPY-MUNCH INTEGRATION SERVICE")
    print("=" * 60)
    print("✅ Full Production Mode - Real API Integration")
    print()
    print(f"🌐 Service URL: http://localhost:{port}")
    print(f"💚 Health Check: GET http://localhost:{port}/health")
    print(f"📱 Scan Endpoint: POST http://localhost:{port}/scan")
    print(f"🔗 Webhook: POST http://localhost:{port}/webhook/loopy/enrolled")
    print()
    print("📋 Features:")
    print("  • Real Loopy card lookup by PID")
    print("  • Automatic Munch account creation")
    print("  • Credit application for free coffees")
    print("  • Webhook support for Make.com integration")
    print("  • Duplicate prevention (5-minute cooldown)")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=False) 