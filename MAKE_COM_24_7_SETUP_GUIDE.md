# 🎁 Make.com 24/7 Rewards Webhook Setup Guide

## Overview
This guide sets up **automatic credit application** when customers earn rewards in Loopy, using our **FIXED calculation** (Rewards Earned - Rewards Redeemed).

## 🐛 Critical Fix Applied
- ✅ **FIXED**: Now uses correct calculation `Rewards Earned - Rewards Redeemed`
- ❌ **NO LONGER** uses buggy `stamps ÷ 12` calculation
- 💰 **Impact**: Prevents excess credits like Amanda Gifford's R1,320 → R40 correction

## Architecture

### Two Webhook Types
1. **Enrollment Webhook** (`/webhook/loopy/enrolled`) - Creates new customers in Munch
2. **Rewards Webhook** (`/webhook/rewards-bridge`) - Applies credits automatically when rewards earned

### Service Components
- **Main Service** (Port 5004): `loopy_munch_production_final_UPDATED.py`
- **Rewards Bridge** (Port 5008): `make_com_rewards_bridge.py`

## 🚀 Quick Start

### 1. Start 24/7 Services
```bash
./start_24_7_services.sh
```

This starts both services in the background with logging.

### 2. Verify Services Running
```bash
# Check main service
curl http://localhost:5004/health

# Check rewards bridge
curl http://localhost:5008/health
```

### 3. Check Logs
```bash
tail -f production_service.log
tail -f rewards_bridge_service.log
```

## 🌐 Make.com Configuration

### Scenario 1: Customer Enrollment
- **Trigger**: When customer enrolls in Loopy
- **Webhook URL**: `https://your-domain.com/webhook/loopy/enrolled`
- **Purpose**: Creates customer account in Munch

### Scenario 2: Rewards Earned (NEW)
- **Trigger**: When customer earns rewards in Loopy
- **Webhook URL**: `https://your-domain.com/webhook/rewards-bridge`
- **Purpose**: Automatically applies credits to Munch account

## 📋 Make.com Setup Steps

### For Rewards Automation:

1. **Create New Scenario**
   - Name: "Loopy Rewards → Munch Credits"
   - Trigger: Loopy rewards earned event

2. **Configure Webhook**
   - URL: `https://your-domain.com/webhook/rewards-bridge`
   - Method: POST
   - Content-Type: application/json

3. **Data Mapping**
   - Ensure customer ID/loyalty code is included
   - Map to field: `loyalty_code`, `pid`, `cardId`, or `customer_code`

4. **Test Configuration**
   ```bash
   curl -X POST http://localhost:5008/test-rewards \
     -H "Content-Type: application/json" \
     -d '{"loyalty_code": "test123"}'
   ```

## 🔄 Automatic Flow

### When Customer Earns Rewards:
1. 🎯 Customer reaches reward milestone in Loopy
2. 📡 Loopy sends webhook to Make.com
3. 🌉 Make.com forwards to rewards bridge (port 5008)
4. 🔄 Bridge extracts loyalty code and forwards to main service
5. 🧮 Main service calculates credits using **FIXED formula**
6. 💳 Credits applied automatically to Munch account
7. ✅ Customer can use credits immediately at POS

### Calculation Verification:
```
Example: Amanda Gifford
- Stamps: 398
- Rewards Earned: 33
- Rewards Redeemed: 32
- Available Rewards: 33 - 32 = 1
- Credit Applied: 1 × R40 = R40 ✅
- Old Bug Would Give: 398 ÷ 12 × R40 = R1,320 ❌
```

## 🛠️ Troubleshooting

### Service Not Starting
```bash
# Check if ports are in use
lsof -i :5004
lsof -i :5008

# Kill existing processes
./start_24_7_services.sh  # Script handles this automatically
```

### Webhook Not Receiving Data
1. Check Make.com scenario is active
2. Verify webhook URL is correct
3. Check logs: `tail -f rewards_bridge_service.log`
4. Test endpoint: `curl http://localhost:5008/test-rewards`

### Credits Not Applied
1. Check main service logs: `tail -f production_service.log`
2. Verify Munch API tokens are valid
3. Test health endpoint: `curl http://localhost:5004/health`

### Duplicate Credits
- ✅ **Fixed**: Smart duplicate prevention built-in
- System tracks processed rewards to prevent duplicates
- No action needed - handled automatically

## 📊 Monitoring

### Health Checks
```bash
# Main service health
curl http://localhost:5004/health | jq

# Rewards bridge health  
curl http://localhost:5008/health | jq
```

### Log Monitoring
```bash
# Real-time logs
tail -f production_service.log rewards_bridge_service.log

# Search for specific customer
grep "Amanda Gifford" production_service.log
```

### Test Rewards Processing
```bash
# Test with real customer code
curl -X POST http://localhost:5008/webhook/rewards-bridge \
  -H "Content-Type: application/json" \
  -d '{"loyalty_code": "cAJlVPWsqDGeCE"}'
```

## 🔒 Security

### Webhook Security
- Services run on localhost (not exposed)
- Use reverse proxy (nginx/cloudflare) for HTTPS
- Consider webhook signature verification for production

### API Tokens
- Munch tokens stored in `munch_tokens.json`
- Loopy config in `WORKING_MUNCH_API_CONFIG.json`
- Keep these files secure and backed up

## 📈 Performance

### Expected Load
- **Enrollment**: Low frequency (new customers)
- **Rewards**: Medium frequency (customers earning rewards)
- **Processing Time**: < 2 seconds per webhook

### Scaling
- Services are stateless (except SQLite tracking DB)
- Can run multiple instances behind load balancer
- Database handles concurrent access safely

## ✅ Verification Checklist

- [ ] Both services start successfully
- [ ] Health checks return 200 OK
- [ ] Make.com scenarios configured
- [ ] Webhook URLs updated
- [ ] Test webhooks working
- [ ] Logs show successful processing
- [ ] Credits applied correctly in Munch
- [ ] No duplicate credits created

## 🎯 Success Metrics

### Before Fix (Buggy Calculation)
- Amanda Gifford: R1,320 (incorrect)
- 233 customers affected
- R39,720 total excess credits

### After Fix (Correct Calculation)
- Amanda Gifford: R40 (correct)
- All excess credits withdrawn
- Automatic 24/7 operation

The system now operates correctly with proper accounting and no manual intervention required! 