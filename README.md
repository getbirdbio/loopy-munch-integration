# 🏪 Loopy-Munch POS Integration

[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)](https://github.com/your-username/loopy-munch-integration)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Automate free coffee redemptions by integrating Loopy Loyalty with Munch POS**

## 🎯 Overview

This integration automatically processes loyalty card scans from Loopy Loyalty app and creates account credits in Munch POS system, eliminating manual cashier work for free coffee redemptions.

### 🔄 Customer Flow
1. **Customer scans** Loopy loyalty card (12 stamps = 1 free coffee)
2. **Loopy sends webhook** to Make.com automation platform
3. **Make.com forwards** to your integration service
4. **Service processes** customer lookup and reward calculation
5. **Automatic credit** applied to Munch POS customer account
6. **Cashier processes** coffee order using customer account balance

## ✨ Features

- 🔗 **Real-time integration** with Loopy Loyalty API
- 💳 **Automatic Munch account** creation for new customers  
- 💰 **Credit application** (R40 per free coffee earned)
- 🛡️ **Duplicate prevention** with 5-minute cooldown
- 📊 **Comprehensive logging** and error handling
- 🌐 **Webhook support** for Make.com automation
- 🔒 **Secure credential** management

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Loopy Loyalty account with API access
- Munch POS account with API access
- Make.com account for webhook automation
- ngrok for local tunnel (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/loopy-munch-integration.git
   cd loopy-munch-integration
   ```

2. **Set up credentials**
   ```bash
   cp munch_tokens.json.template munch_tokens.json
   cp production.env.template production.env
   # Edit both files with your real API credentials
   ```

3. **Start the service**
   ```bash
   chmod +x start_integration.sh
   ./start_integration.sh
   ```

4. **Set up ngrok tunnel** (for webhook access)
   ```bash
   ngrok http 5004 --domain=your-domain.ngrok.app
   ```

## 📋 Configuration

### API Credentials Required

#### Loopy Loyalty
- API Key
- Username/Password  
- Campaign ID

#### Munch POS
- Bearer Token
- Organization ID

### Make.com Webhook Setup

Configure HTTP module to forward webhooks:
- **URL:** `https://your-domain.ngrok.app/webhook/loopy/enrolled`
- **Method:** `POST`
- **Content-Type:** `application/json`
- **Body:** `{"pid": "{{1.Bundle.value.pid}}"}`

## 🧪 Testing

### Health Check
```bash
curl http://localhost:5004/health
```

### Manual Webhook Test
```bash
curl -X POST http://localhost:5004/webhook/loopy/enrolled \
  -H "Content-Type: application/json" \
  -d '{"pid": "YOUR_TEST_PID"}'
```

## 📁 Project Structure

```
loopy-munch-integration/
├── loopy_munch_production_final.py    # Main service
├── start_integration.sh               # Startup script
├── LOOPY_MUNCH_INTEGRATION_FINAL.md   # Complete documentation
├── README.md                          # This file
├── .gitignore                         # Git ignore rules
├── munch_tokens.json.template         # Credentials template
├── production.env.template            # Environment template
└── requirements.txt                   # Python dependencies
```

## 🔧 Service Endpoints

- **Health Check:** `GET /health`
- **Manual Scan:** `POST /scan`
- **Webhook:** `POST /webhook/loopy/enrolled`

## 📊 Monitoring

Monitor service logs for real-time activity:
- ✅ Successful processing indicators
- ❌ Error conditions and troubleshooting
- 📈 Customer redemption analytics

## 🛟 Troubleshooting

### Common Issues

1. **Service not starting**
   - Check Python dependencies
   - Verify credentials in config files
   - Ensure port 5004 is available

2. **Webhook not receiving data**
   - Verify Make.com configuration
   - Check ngrok tunnel status
   - Test with manual webhook calls

3. **API authentication failures**
   - Validate Loopy API credentials
   - Check Munch bearer token expiry
   - Review credential file formats

## 📈 Production Deployment

### Requirements
- Persistent server environment
- SSL certificate for webhook endpoint
- Process monitoring (PM2, systemd, etc.)
- Log rotation and monitoring

### Deployment Checklist
- [ ] Server environment configured
- [ ] SSL certificate installed
- [ ] Credentials securely stored
- [ ] Service auto-restart configured
- [ ] Monitoring and alerting set up
- [ ] Backup and recovery procedures

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support and questions:
- 📧 **Email:** your-email@domain.com
- 📱 **Phone:** +27-XXX-XXX-XXX
- 🐛 **Issues:** [GitHub Issues](https://github.com/your-username/loopy-munch-integration/issues)

## 🎉 Acknowledgments

- **Loopy Loyalty** for the loyalty platform API
- **Munch POS** for the point-of-sale integration
- **Make.com** for webhook automation platform

---

**Made with ☕ for automated coffee redemptions** 