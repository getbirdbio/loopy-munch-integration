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
        
        # Check environment variables
        env_checks = {
            'munch_api_key': bool(os.getenv('MUNCH_API_KEY')),
            'munch_org_id': bool(os.getenv('MUNCH_ORG_ID')),
            'webhook_url': bool(os.getenv('WEBHOOK_URL')),
            'rewards_webhook_url': bool(os.getenv('REWARDS_WEBHOOK_URL')),
            'campaign_id': bool(os.getenv('CAMPAIGN_ID'))
        }
        
        # Overall health status
        all_configured = all(env_checks.values())
        health_status = 'healthy' if all_configured else 'warning'
        
        response = {
            'status': health_status,
            'service': 'loopy_munch_integration',
            'version': '2.0.0',
            'timestamp': datetime.now().isoformat(),
            'environment_checks': env_checks,
            'configuration_summary': {
                'total_env_vars': len(env_checks),
                'configured_count': sum(env_checks.values()),
                'missing_count': len(env_checks) - sum(env_checks.values()),
                'all_configured': all_configured
            },
            'deployment_info': {
                'platform': 'vercel',
                'runtime': 'python3.9',
                'mode': 'serverless_functions'
            },
            'message': '✅ All systems operational!' if all_configured else '⚠️  Some environment variables missing'
        }
        
        self.wfile.write(json.dumps(response, indent=2).encode())
        return 