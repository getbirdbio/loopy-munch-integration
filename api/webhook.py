import json
import os
import requests
from datetime import datetime

def handler(request):
    """Vercel serverless function for handling webhooks"""
    
    # Get request data
    if hasattr(request, 'get_json'):
        data = request.get_json() or {}
    else:
        try:
            data = json.loads(request.body) if hasattr(request, 'body') else {}
        except:
            data = {}
    
    # Basic webhook processing
    response = {
        'status': 'success',
        'message': 'Webhook received',
        'timestamp': datetime.now().isoformat(),
        'data_received': bool(data)
    }
    
    # Process if it's a rewards webhook
    if 'card' in data:
        card_data = data.get('card', {})
        total_stamps = card_data.get('totalStampsEarned', 0)
        customer_details = card_data.get('customerDetails', {})
        customer_email = customer_details.get('email')
        
        free_coffees = total_stamps // 12  # 12 stamps per coffee
        
        if free_coffees > 0 and customer_email:
            response.update({
                'customer_email': customer_email,
                'total_stamps': total_stamps,
                'free_coffees': free_coffees,
                'credit_amount': free_coffees * 40
            })
            
            # Forward to Make.com
            webhook_url = os.getenv('REWARDS_WEBHOOK_URL')
            if webhook_url:
                try:
                    make_response = requests.post(webhook_url, json=data, timeout=10)
                    response['forwarded_to_make'] = {
                        'success': make_response.status_code == 200,
                        'status_code': make_response.status_code
                    }
                except Exception as e:
                    response['forwarded_to_make'] = {
                        'success': False,
                        'error': str(e)
                    }
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(response)
    } 