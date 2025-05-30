#!/bin/bash

# Cloudflare Tunnel Setup - FREE fixed URL!
# Provides a permanent URL that doesn't change

echo "🌩️  Setting up Cloudflare Tunnel for fixed URL"
echo "=============================================="

# Step 1: Install cloudflared
echo "1. Installing cloudflared..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    if ! command -v cloudflared &> /dev/null; then
        echo "Installing cloudflared via Homebrew..."
        brew install cloudflared
    else
        echo "✅ cloudflared already installed"
    fi
else
    # Linux
    wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    sudo dpkg -i cloudflared-linux-amd64.deb
fi

# Step 2: Login to Cloudflare
echo "2. Login to Cloudflare (this will open a browser)..."
cloudflared tunnel login

# Step 3: Create tunnel
echo "3. Creating tunnel..."
TUNNEL_NAME="loopy-munch-$(date +%Y%m%d)"
cloudflared tunnel create $TUNNEL_NAME

# Step 4: Get tunnel ID
TUNNEL_ID=$(cloudflared tunnel list | grep $TUNNEL_NAME | awk '{print $1}')
echo "Tunnel ID: $TUNNEL_ID"

# Step 5: Create DNS record
echo "4. Setting up DNS..."
echo "Please enter your domain (e.g., yourdomain.com):"
read DOMAIN
SUBDOMAIN="loopy-munch"
cloudflared tunnel route dns $TUNNEL_ID $SUBDOMAIN.$DOMAIN

# Step 6: Create config file
echo "5. Creating config file..."
mkdir -p ~/.cloudflared
cat > ~/.cloudflared/config.yml << EOF
tunnel: $TUNNEL_ID
credentials-file: ~/.cloudflared/$TUNNEL_ID.json

ingress:
  - hostname: $SUBDOMAIN.$DOMAIN
    service: http://localhost:5004
  - service: http_status:404
EOF

echo "✅ Setup complete!"
echo "Your fixed URL will be: https://$SUBDOMAIN.$DOMAIN"
echo ""
echo "To start the tunnel:"
echo "cloudflared tunnel run $TUNNEL_NAME" 