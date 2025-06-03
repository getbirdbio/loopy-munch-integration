import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            'status': 'healthy',
            'service': 'loopy_munch_integration',
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat(),
            'message': 'Vercel deployment successful!',
            'endpoints': {
                'health': '/api/health',
                'webhook_rewards': '/api/webhook',
                'root': '/api/index'
            }
        }
        
        self.wfile.write(json.dumps(response).encode())
        return 