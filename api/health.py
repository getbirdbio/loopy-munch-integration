import json
import os
from datetime import datetime

def handler(request):
    """Vercel serverless function for health check"""
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
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
            'mode': 'vercel_serverless',
            'message': 'Vercel deployment working!'
        })
    } 