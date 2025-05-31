#!/usr/bin/env python3
"""
Make.com Rewards Bridge - 24/7 Automatic Credit Application
==========================================================
This bridge handles Loopy rewards webhooks from Make.com and automatically
applies credits to Munch accounts using our FIXED calculation.

CRITICAL: Uses FIXED calculation (Rewards Earned - Rewards Redeemed)
NOT the buggy stamps/12 calculation.
"""

from flask import Flask, request, jsonify
import requests
import json
import logging
from datetime import datetime

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Production service URL (using our FIXED calculation service)
PRODUCTION_SERVICE_URL = "http://localhost:5004"

@app.route('/webhook/rewards-bridge', methods=['POST'])
def rewards_bridge():
    """Bridge endpoint for Make.com rewards webhooks - triggers automatic credit application"""
    
    logger.info("=" * 70)
    logger.info("🎁 REWARDS WEBHOOK RECEIVED FROM MAKE.COM")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Content-Type: {request.content_type}")
    logger.info(f"Raw Data: {request.data}")
    logger.info(f"Data as Text: {request.get_data(as_text=True)}")
    logger.info("=" * 70)
    
    try:
        # Extract customer/loyalty data from Make.com
        loyalty_code = None
        customer_data = {}
        
        # Method 1: Try JSON parsing
        try:
            if request.content_type == 'application/json':
                data = request.get_json(force=True)
                logger.info(f"📊 Parsed JSON: {data}")
                
                if isinstance(data, dict):
                    # Extract loyalty code from various fields
                    loyalty_code = (
                        data.get('pid') or 
                        data.get('cardId') or 
                        data.get('loyalty_code') or
                        data.get('customer_code') or
                        data.get('id')
                    )
                    
                    # Check nested card object
                    if not loyalty_code and 'card' in data:
                        card = data['card']
                        if isinstance(card, dict):
                            loyalty_code = card.get('id') or card.get('pid')
                    
                    # Store full customer data
                    customer_data = data
                    
                elif isinstance(data, str):
                    # Sometimes Make.com sends just the loyalty code as a string
                    loyalty_code = data.strip().replace('"', '')
                    
                elif isinstance(data, (int, float)):
                    # Sometimes Make.com sends numbers
                    loyalty_code = str(data)
                    
        except Exception as e:
            logger.warning(f"JSON parsing failed: {e}")
        
        # Method 2: Try extracting from raw text
        if not loyalty_code:
            raw_text = request.get_data(as_text=True)
            if raw_text and len(raw_text.strip()) > 5:
                # Remove quotes and whitespace
                cleaned = raw_text.strip().replace('"', '').replace("'", '')
                # Check if it looks like a loyalty code (alphanumeric, reasonable length)
                if 10 <= len(cleaned) <= 20 and cleaned.replace('_', '').replace('-', '').isalnum():
                    loyalty_code = cleaned
        
        # Method 3: Check URL parameters
        if not loyalty_code:
            loyalty_code = (
                request.args.get('pid') or 
                request.args.get('cardId') or 
                request.args.get('loyalty_code')
            )
        
        logger.info(f"🎯 Extracted loyalty code: {loyalty_code}")
        
        if not loyalty_code:
            logger.error("❌ NO LOYALTY CODE FOUND - Make.com configuration issue!")
            return jsonify({
                "error": "no_loyalty_code_found",
                "message": "Could not extract loyalty code from Make.com rewards webhook",
                "received_data": request.get_data(as_text=True),
                "headers": dict(request.headers),
                "help": "Check Make.com rewards webhook configuration"
            }), 400
        
        # Create rewards webhook payload for our production service
        rewards_payload = {
            "loyalty_code": loyalty_code,
            "event_type": "rewards_earned",
            "webhook_source": "make_com_rewards",
            "timestamp": datetime.now().isoformat(),
            "customer_data": customer_data
        }
        
        logger.info(f"🚀 Forwarding to REWARDS webhook: {rewards_payload}")
        
        # Forward to our FIXED production service rewards endpoint
        response = requests.post(
            f"{PRODUCTION_SERVICE_URL}/webhook/loopy/rewards",
            json=rewards_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Rewards processing response: {result}")
            
            # Check if credits were applied
            if result.get("success") and result.get("credit_applied"):
                logger.info(f"🎉 AUTOMATIC CREDIT APPLIED!")
                logger.info(f"   Customer: {result.get('customer_name', 'Unknown')}")
                logger.info(f"   Credit: R{result.get('credit_amount', 0)}")
                logger.info(f"   Calculation: {result.get('calculation_method', 'Unknown')}")
            else:
                logger.info(f"ℹ️  No new credits needed: {result.get('message', 'Unknown')}")
            
            return jsonify({
                "bridge_status": "success",
                "loyalty_code": loyalty_code,
                "automatic_processing": True,
                "production_response": result,
                "message": "Rewards webhook processed successfully"
            })
        else:
            logger.error(f"❌ Production service error: {response.status_code} - {response.text}")
            return jsonify({
                "bridge_status": "production_error",
                "loyalty_code": loyalty_code,
                "error": f"Production service returned {response.status_code}",
                "response": response.text
            }), 502
            
    except Exception as e:
        logger.error(f"❌ Rewards bridge error: {e}")
        return jsonify({
            "bridge_status": "error",
            "error": str(e),
            "received_data": request.get_data(as_text=True),
            "webhook_type": "rewards"
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check for rewards bridge"""
    return jsonify({
        "status": "healthy",
        "service": "make_com_rewards_bridge",
        "webhook_type": "rewards",
        "production_service": PRODUCTION_SERVICE_URL,
        "calculation_method": "FIXED - Rewards Earned - Rewards Redeemed",
        "purpose": "24/7 automatic credit application when customers earn rewards"
    })

@app.route('/test-rewards', methods=['POST', 'GET'])
def test_rewards_endpoint():
    """Test endpoint for rewards webhook"""
    
    logger.info("=" * 50)
    logger.info("🧪 REWARDS WEBHOOK TEST")
    logger.info(f"Method: {request.method}")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Raw Data: {request.data}")
    logger.info(f"Args: {dict(request.args)}")
    logger.info("=" * 50)
    
    try:
        if request.method == 'POST':
            data = request.get_json(force=True) if request.data else {}
            logger.info(f"JSON Data: {data}")
        else:
            data = dict(request.args)
            
        return jsonify({
            "test_status": "success",
            "webhook_type": "rewards",
            "method": request.method,
            "headers": dict(request.headers),
            "data": data,
            "raw": request.get_data(as_text=True),
            "message": "Rewards webhook test completed"
        })
        
    except Exception as e:
        return jsonify({
            "test_status": "error",
            "error": str(e),
            "raw_data": request.get_data(as_text=True)
        })

if __name__ == '__main__':
    print("🎁 MAKE.COM REWARDS BRIDGE - 24/7 AUTOMATIC CREDIT APPLICATION")
    print("=" * 70)
    print("🐛 FIXED CALCULATION: Uses Rewards Earned - Rewards Redeemed")
    print("❌ NO LONGER uses buggy stamps/12 calculation")
    print()
    print("🌐 Endpoints:")
    print("   🎁 Rewards Bridge: POST /webhook/rewards-bridge")
    print("   🧪 Test Rewards:   POST /test-rewards")
    print("   💚 Health:         GET  /health")
    print()
    print("🔄 Automatic Flow:")
    print("   1. Customer earns rewards in Loopy")
    print("   2. Loopy sends webhook to Make.com")
    print("   3. Make.com forwards to this bridge")
    print("   4. Bridge triggers automatic credit application")
    print("   5. Credits applied to Munch account instantly")
    print()
    print("🌐 Port: 5008")
    print("=" * 70)
    print()
    print("📋 Setup Instructions:")
    print("1. In Make.com, create a new scenario for 'Rewards Earned' events")
    print("2. Set webhook URL to: https://your-domain.com/webhook/rewards-bridge")
    print("3. Configure to trigger when customers earn rewards (not enrollment)")
    print("4. Test with: curl -X POST http://localhost:5008/test-rewards")
    print()
    
    app.run(host='0.0.0.0', port=5008, debug=True) 