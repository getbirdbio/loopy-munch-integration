import json
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # Get base URL from request
        host = self.headers.get('Host', 'localhost')
        protocol = 'https' if 'vercel.app' in host else 'http'
        base_url = f"{protocol}://{host}"
        
        response = {
            'status': 'healthy',
            'service': 'loopy_munch_integration',
            'version': '2.0.0',
            'timestamp': datetime.now().isoformat(),
            'message': 'Vercel deployment successful! ✅',
            'base_url': base_url,
            'endpoints': {
                'health_check': f"{base_url}/health",
                'api_root': f"{base_url}/api/index",
                'webhook_handler': f"{base_url}/api/webhook",
                'loopy_webhooks': {
                    'rewards': f"{base_url}/webhook/rewards", 
                    'enrolled': f"{base_url}/webhook/enrolled",
                    'stamp': f"{base_url}/webhook/stamp"
                }
            },
            'configuration': {
                'munch_api_configured': bool(os.getenv('MUNCH_API_KEY')),
                'webhook_configured': bool(os.getenv('WEBHOOK_URL')),
                'rewards_webhook_configured': bool(os.getenv('REWARDS_WEBHOOK_URL')),
                'campaign_configured': bool(os.getenv('CAMPAIGN_ID'))
            },
            'usage': {
                'test_webhook': f"curl -X POST {base_url}/webhook/rewards -H 'Content-Type: application/json' -d '{{\"test\": true}}'",
                'health_check': f"curl {base_url}/health"
            }
        }
        
        self.wfile.write(json.dumps(response, indent=2).encode())
        return 