from flask import Flask, jsonify
import os
from datetime import datetime

app = Flask(__name__)

@app.route('/health')
@app.route('/')
def health():
    return jsonify({
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

# Vercel expects this
def handler(request):
    return app(request.environ, lambda status, headers: None) 