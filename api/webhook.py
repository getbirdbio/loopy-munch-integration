import json
import os
import requests
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests for Loopy webhooks"""
        try:
            # Internal API Authentication
            internal_auth_token = os.getenv('INTERNAL_API_AUTH_TOKEN')
            if internal_auth_token:  # Only authenticate if token is configured
                auth_header = self.headers.get('X-Internal-Auth-Token')
                if not auth_header or auth_header != internal_auth_token:
                    self.send_response(401)
                    self.send_header('Content-type', 'application/json')
                    # No Access-Control-Allow-Origin for 401 response
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'status': 'error',
                        'message': 'Unauthorized'
                    }).encode())
                    return

            # Get content length
            content_length = int(self.headers.get('Content-Length', 0))
            
            # Read request body
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
            else:
                data = {}
            
            # Parse path to get endpoint
            parsed_path = urlparse(self.path)
            path_parts = parsed_path.path.strip('/').split('/')
            
            # Extract endpoint (e.g., "rewards", "enrolled", "stamp")
            endpoint = None
            if 'webhook' in path_parts:
                webhook_index = path_parts.index('webhook')
                if webhook_index + 1 < len(path_parts):
                    endpoint = path_parts[webhook_index + 1]
            
            # Basic webhook processing
            response = {
                'status': 'success',
                'message': 'Webhook received',
                'timestamp': datetime.now().isoformat(),
                'endpoint': endpoint,
                'data_received': bool(data),
                'path': self.path
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
            
            # Send successful response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            # No Access-Control-Allow-Origin for POST success response
            # No Access-Control-Allow-Methods for POST success response
            # No Access-Control-Allow-Headers for POST success response
            self.end_headers()
            
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            # Send error response
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            # No Access-Control-Allow-Origin for 500 response
            self.end_headers()
            
            error_response = {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_GET(self):
        """Handle GET requests for webhook info"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            'status': 'ready',
            'service': 'loopy_webhook_handler',
            'message': 'Webhook endpoint ready to receive POST requests',
            'available_endpoints': [
                '/api/webhook/rewards',
                '/api/webhook/enrolled',
                '/api/webhook/stamp'
            ],
            'timestamp': datetime.now().isoformat()
        }
        
        self.wfile.write(json.dumps(response).encode())
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        # Ensure X-Internal-Auth-Token is allowed if you plan to use it with GET/OPTIONS too
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Internal-Auth-Token')
        self.end_headers() 