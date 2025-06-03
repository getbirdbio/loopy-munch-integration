import json
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            'status': 'healthy',
            'service': 'loopy_make_integration',
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat(),
            'configuration': {
                'munch_api_configured': bool(os.getenv('MUNCH_API_KEY')),
                'webhook_configured': bool(os.getenv('WEBHOOK_URL')),
                'rewards_webhook_configured': bool(os.getenv('REWARDS_WEBHOOK_URL')),
                'campaign_configured': bool(os.getenv('CAMPAIGN_ID'))
            },
            'mode': 'vercel_simple_handler',
            'message': 'Vercel deployment working!'
        }
        
        self.wfile.write(json.dumps(response).encode())
        return 