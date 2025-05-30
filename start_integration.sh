#!/bin/bash

# Loopy-Munch Integration Startup Script
# Created: May 30, 2025
# Status: Production Ready

echo "🚀 Starting Loopy-Munch Integration Service..."
echo "=============================================="

# Check if service is already running
if pgrep -f "loopy_munch_production_final.py" > /dev/null; then
    echo "⚠️  Service already running. Stopping existing process..."
    pkill -f "loopy_munch_production_final.py"
    sleep 2
fi

# Set environment and start service
export SERVICE_PORT=5004
echo "✅ Starting service on port 5004..."
python3 loopy_munch_production_final.py &

# Wait for service to start
sleep 3

# Health check
echo "🔍 Performing health check..."
if curl -s http://localhost:5004/health | jq -e '.status == "healthy"' > /dev/null; then
    echo "✅ Service is healthy and running!"
    echo ""
    echo "📋 Service Information:"
    echo "   • Local URL: http://localhost:5004"
    echo "   • Health Check: http://localhost:5004/health" 
    echo "   • Webhook: http://localhost:5004/webhook/loopy/enrolled"
    echo ""
    echo "🌐 With ngrok (fixed domain):"
    echo "   • Public URL: https://api.getbird.co.za"
    echo "   • Health Check: https://api.getbird.co.za/health"
    echo "   • Webhook: https://api.getbird.co.za/webhook/loopy/enrolled"
    echo ""
    echo "🎯 Integration is LIVE and ready for customers!"
    echo "   Monitor logs for real-time activity."
else
    echo "❌ Health check failed. Check logs for errors."
    exit 1
fi

echo ""
echo "💡 To start ngrok tunnel:"
echo "   ngrok http 5004 --domain=api.getbird.co.za"
echo ""
echo "🛑 To stop service:"
echo "   pkill -f loopy_munch_production_final.py" 