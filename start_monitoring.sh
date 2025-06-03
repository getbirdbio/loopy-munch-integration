#!/bin/bash

echo "🔍 LOOPY-MAKE.COM INTEGRATION MONITOR"
echo "====================================="
echo ""
echo "Choose monitoring option:"
echo ""
echo "1. 📋 Live Logs (real-time service logs)"
echo "2. 📊 Interactive Monitor (send tests & check status)"
echo "3. 🧪 Quick Status Check"
echo "4. 📝 View Recent Activity"
echo ""
read -p "Enter choice (1-4): " choice

case $choice in
    1)
        echo ""
        echo "📋 LIVE LOGS - Press Ctrl+C to stop"
        echo "======================================"
        tail -f service_logs.txt
        ;;
    2)
        echo ""
        echo "📊 INTERACTIVE MONITOR"
        echo "======================"
        source venv/bin/activate
        python monitor_system.py
        ;;
    3)
        echo ""
        echo "🧪 QUICK STATUS CHECK"
        echo "===================="
        source venv/bin/activate
        python -c "
from monitor_system import SystemMonitor
import json
m = SystemMonitor()
print(f'🕐 {__import__(\"datetime\").datetime.now().strftime(\"%H:%M:%S\")}')
print(f'Local Service:  {m.get_service_status()}')
print(f'Domain Access:  {m.get_domain_status()}')
print()
print('📊 Testing webhook...')
result = m.send_test_webhook('enrolled')
if result.get('success'):
    print(f'✅ Webhook Test: SUCCESS ({result[\"status\"]})')
else:
    print(f'❌ Webhook Test: FAILED')
"
        ;;
    4)
        echo ""
        echo "📝 RECENT ACTIVITY (last 10 log entries)"
        echo "========================================"
        tail -10 service_logs.txt
        echo ""
        echo "📈 Process Status:"
        ps aux | grep loopy_make_integration | grep -v grep || echo "❌ Service not running"
        ;;
    *)
        echo "Invalid choice"
        ;;
esac 