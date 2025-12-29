# 🚀 Streamlit Cloud Deployment Guide

This guide will help you deploy FleetGuardAI to Streamlit Cloud.

---

## 📋 Prerequisites

1. ✅ GitHub account with your FleetGuardAI repository
2. ✅ Streamlit Cloud account (free at [share.streamlit.io](https://share.streamlit.io))
3. ✅ OpenAI API key (get from [platform.openai.com/api-keys](https://platform.openai.com/api-keys))

---

## 🔐 Step 1: Configure Secrets in Streamlit Cloud

**IMPORTANT:** Your OpenAI API key and email credentials are NOT included in the GitHub repository for security reasons. You must add them manually in Streamlit Cloud.

### How to Add Secrets:

1. **Deploy your app** to Streamlit Cloud (connect to your GitHub repo)
2. **Go to App Settings** → Click the "⋮" menu → Select "Settings"
3. **Navigate to Secrets** → Click the "Secrets" tab
4. **Copy the template** from `.streamlit/secrets.toml.example`
5. **Paste and modify** with your actual values:

```toml
# Required: OpenAI API Key
OPENAI_API_KEY = "sk-proj-YOUR-ACTUAL-KEY-HERE"
OPENAI_MODEL_NAME = "gpt-4o-mini"

# Database path (leave as-is)
DATABASE_PATH = "data/database/fleet.db"

# Application settings
ENVIRONMENT = "production"
LOG_LEVEL = "INFO"

# Email features (optional - set to false to disable)
EMAIL_FETCH_ENABLED = false
EMAIL_IMAP_SERVER = "imap.gmail.com"
EMAIL_IMAP_PORT = 993
EMAIL_ADDRESS = "your-email@gmail.com"
EMAIL_PASSWORD = "your-gmail-app-password"
EMAIL_FOLDER = "FleetGuardAI"
EMAIL_MARK_AS_READ = true
EMAIL_MAX_FETCH = 50
EMAIL_DATE_FILTER_DAYS = 30
```

6. **Save changes** → App will automatically reboot with new secrets

---

## 🔑 Step 2: Get OpenAI API Key

1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Click "Create new secret key"
3. Copy the key (starts with `sk-proj-...`)
4. Add it to Streamlit Secrets as shown above

**Cost Estimate:** With GPT-4o-mini, typical usage costs < $1/month for demo purposes.

---

## 📧 Step 3: Email Configuration (Optional)

If you want email invoice syncing to work:

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password:**
   - Go to [Google Account Settings](https://myaccount.google.com/)
   - Security → 2-Step Verification → App Passwords
   - Generate password for "Mail" app
3. **Add credentials** to Streamlit Secrets (see Step 1)
4. **Set `EMAIL_FETCH_ENABLED = true`** in secrets

**Note:** Email syncing is optional. The app works without it using the pre-loaded database.

---

## ✅ Step 4: Verify Deployment

After configuring secrets:

1. **App should automatically reboot** (takes 1-2 minutes)
2. **Check deployment logs** in Streamlit Cloud dashboard
3. **Test the app:**
   - Login should work (credentials stored in database)
   - Dashboard should display fleet data
   - Chatbot should respond (requires OpenAI API key)

---

## 🔍 Troubleshooting

### Issue: "No database found" error

**Solution:**
- The database `fleet.db` is now included in the repository
- If you still see this error, check that the latest commit is deployed
- Force a reboot: App Settings → "⋮" → "Reboot app"

### Issue: Chatbot not responding

**Cause:** Missing or invalid OpenAI API key

**Solution:**
1. Check Streamlit Secrets has `OPENAI_API_KEY` set
2. Verify the key is valid at [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
3. Reboot the app after updating secrets

### Issue: Email sync failing

**Cause:** Email credentials not configured or incorrect

**Solution:**
1. Set `EMAIL_FETCH_ENABLED = false` in Streamlit Secrets to disable email features
2. Or, configure valid Gmail credentials (see Step 3)

### Issue: Import errors

**Cause:** Path resolution issues in Streamlit Cloud

**Solution:**
- The `streamlit_app.py` entry point handles path resolution
- Ensure you're using the latest code from GitHub
- Check deployment logs for specific error messages

---

## 📊 Default Demo Data

The app comes pre-loaded with demo data:

- **86 vehicles** with realistic attributes
- **1,013 invoices** spanning multiple months
- **Sample users** for testing (username: `admin`, password: `admin123`)

You can modify this data locally by running `python FleetGuard/generate_data.py` and committing the updated database.

---

## 🔄 Updating Your Deployment

When you push changes to GitHub:

1. **Automatic deployment** - Streamlit Cloud detects changes
2. **Rebuilds app** - Usually takes 2-5 minutes
3. **App restarts** - Your changes go live automatically

No manual intervention needed!

---

## 🛡️ Security Notes

- ✅ **API keys removed** from code repository
- ✅ **Passwords hashed** in database (SHA256)
- ✅ **Secrets managed** via Streamlit Cloud (not in Git)
- ✅ **Email password** uses Gmail App Password (not real password)

---

## 📞 Support

If you encounter issues:

1. Check Streamlit Cloud deployment logs
2. Review this guide's troubleshooting section
3. Contact: adiy2603@gmail.com

---

**Last Updated:** December 30, 2025
**Version:** 2.0.1
