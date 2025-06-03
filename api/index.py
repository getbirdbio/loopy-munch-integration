import json
from datetime import datetime

def handler(request):
    """Vercel serverless function for the main API"""
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'status': 'healthy',
            'service': 'loopy_munch_integration',
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat(),
            'message': 'Vercel deployment successful!',
            'endpoints': {
                'health': '/health',
                'webhook_rewards': '/webhook/loopy/rewards',
                'webhook_enrollment': '/webhook/loopy/enrolled'
            }
        })
    } 