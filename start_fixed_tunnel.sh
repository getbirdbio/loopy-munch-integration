#!/bin/bash

# Simple fixed tunnel using localhost.run (FREE!)
# Provides a consistent subdomain

echo "🌐 Starting fixed tunnel for Loopy-Munch integration"
echo "=================================================="

# Option 1: localhost.run with custom subdomain
SUBDOMAIN="loopy-munch-$(whoami)"
echo "🚀 Starting tunnel with subdomain: $SUBDOMAIN"
echo "Fixed URL will be: https://$SUBDOMAIN.lhr.life"
echo ""
echo "Update your Make.com webhook to: https://$SUBDOMAIN.lhr.life/webhook/loopy/enrolled"
echo ""

# Start the tunnel
ssh -R $SUBDOMAIN:80:localhost:5004 nokey@localhost.run

# Alternative: Use bore.pub (another free option)
# echo "🚀 Alternative: Using bore.pub"
# bore local 5004 --to bore.pub 