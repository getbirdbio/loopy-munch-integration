# 🎨 DEPLOY TO RENDER (FREE ALTERNATIVE)

## 🚀 **5-MINUTE FREE DEPLOYMENT**

### **Step 1: Prepare Code (Already Done!)**
```bash
# Your code is ready with:
✅ Dockerfile
✅ requirements.txt  
✅ production.env
✅ loopy_make_integration.py
```

### **Step 2: Deploy to Render**
1. **Go to [render.com](https://render.com)**
2. **Sign up with GitHub**
3. **New → Web Service**
4. **Connect your repository**
5. **Configuration:**
   ```
   Name: loopy-munch-integration
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: python loopy_make_integration.py
   ```

### **Step 3: Add Environment Variables**
In Render dashboard, add these from your `production.env`:
```
MUNCH_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
MUNCH_ORG_ID=1476d7a5-b7b2-4b18-85c6-33730cf37a12
WEBHOOK_URL=https://hook.eu2.make.com/2mprzrfbiu0pu49rdfisd5xht7ie72pt
REWARDS_WEBHOOK_URL=https://hook.eu2.make.com/d13g4o1ux11ndov624u2p3w3h0lqedn5
CAMPAIGN_ID=hZd5mudqN2NiIrq2XoM46
SERVICE_PORT=5008
```

### **Step 4: Deploy!**
- Click "Create Web Service"
- Wait 2-3 minutes for deployment
- Get your URL: `https://your-app.onrender.com`

### **Step 5: Update Loopy**
Configure Loopy webhooks to:
```
https://your-app.onrender.com/webhook/loopy/rewards
https://your-app.onrender.com/webhook/loopy/enrolled
```

---

## ⚡ **RENDER vs RAILWAY**

| Feature | Render FREE | Railway $5 |
|---------|-------------|------------|
| **Cost** | $0 | $5/month |
| **Always On** | ❌ (sleeps 15min) | ✅ |
| **Setup Time** | 2 min | 3 min |
| **Custom Domain** | ✅ | ✅ |
| **Auto Deploy** | ✅ | ✅ |
| **Monitoring** | Basic | Advanced |

---

## 💡 **RENDER FREE TIER GOTCHA**
The free tier **sleeps after 15 minutes** of inactivity. For a webhook service, this means:

**❌ Problem:** First webhook after sleep = 30-60 second delay
**✅ Solution:** Upgrade to $7/month for always-on

---

## 🎯 **RECOMMENDATION FOR YOU**

Based on your Loopy integration:

1. **Start with Render FREE** to test everything works
2. **Upgrade to Render $7/month** or **switch to DigitalOcean $5/month** for production
3. **Scale to AWS/Heroku** when you have multiple locations

**Your webhook service needs to be always-on for instant loyalty rewards!** 