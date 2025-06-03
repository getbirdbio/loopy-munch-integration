from flask import Flask, jsonify
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
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

# Vercel expects this
def handler(request):
    return app(request.environ, lambda status, headers: None) 