#!/bin/bash

echo "🚀 STARTING 24/7 LOOPY-MUNCH SERVICES WITH FIXED CALCULATION"
echo "=" * 70
echo "🐛 FIXED: Now uses correct calculation (Rewards Earned - Rewards Redeemed)"
echo "❌ NO LONGER uses buggy stamps/12 calculation"
echo ""

# Check if required files exist
if [ ! -f "loopy_munch_production_final_UPDATED.py" ]; then
    echo "❌ ERROR: loopy_munch_production_final_UPDATED.py not found!"
    exit 1
fi

if [ ! -f "make_com_rewards_bridge.py" ]; then
    echo "❌ ERROR: make_com_rewards_bridge.py not found!"
    exit 1
fi

if [ ! -f "WORKING_MUNCH_API_CONFIG.json" ]; then
    echo "❌ ERROR: WORKING_MUNCH_API_CONFIG.json not found!"
    exit 1
fi

if [ ! -f "munch_tokens.json" ]; then
    echo "❌ ERROR: munch_tokens.json not found!"
    exit 1
fi

echo "✅ All required files found"
echo ""

# Function to start a service in the background
start_service() {
    local service_name=$1
    local script_name=$2
    local port=$3
    
    echo "🔄 Starting $service_name on port $port..."
    
    # Kill any existing process on this port
    lsof -ti:$port | xargs kill -9 2>/dev/null || true
    
    # Start the service
    nohup python3 "$script_name" > "${service_name}_service.log" 2>&1 &
    local pid=$!
    
    echo "   PID: $pid"
    echo "   Log: ${service_name}_service.log"
    
    # Wait a moment and check if it's still running
    sleep 2
    if kill -0 $pid 2>/dev/null; then
        echo "   ✅ $service_name started successfully"
    else
        echo "   ❌ $service_name failed to start"
        return 1
    fi
    
    return 0
}

# Start main production service (with FIXED calculation)
start_service "production" "loopy_munch_production_final_UPDATED.py" 5004

# Start rewards bridge service
start_service "rewards_bridge" "make_com_rewards_bridge.py" 5008

echo ""
echo "🌐 SERVICES RUNNING:"
echo "   📊 Main Service:    http://localhost:5004"
echo "   🎁 Rewards Bridge:  http://localhost:5008"
echo ""
echo "🔗 WEBHOOK ENDPOINTS:"
echo "   📝 Enrollment: POST http://localhost:5004/webhook/loopy/enrolled"
echo "   🎁 Rewards:    POST http://localhost:5008/webhook/rewards-bridge"
echo ""
echo "💚 HEALTH CHECKS:"
echo "   curl http://localhost:5004/health"
echo "   curl http://localhost:5008/health"
echo ""
echo "📋 MAKE.COM SETUP:"
echo "1. Enrollment webhook: https://your-domain.com/webhook/loopy/enrolled"
echo "2. Rewards webhook:    https://your-domain.com/webhook/rewards-bridge"
echo ""
echo "🔄 Services are now running 24/7 with FIXED calculation!"
echo "📁 Check logs: production_service.log and rewards_bridge_service.log"
echo "=" * 70 