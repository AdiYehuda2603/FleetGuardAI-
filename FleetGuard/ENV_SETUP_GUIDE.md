# Environment Variables Setup Guide

## 🔐 Setting Up Your OpenAI API Key

Your FleetGuard application now uses a `.env` file to securely store your OpenAI API key.

---

## Quick Setup (3 Steps)

### Step 1: Get Your API Key
1. Go to https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-...`)

### Step 2: Edit the .env File
1. Open the `.env` file in the FleetGuard folder
2. Replace `your-api-key-here` with your actual API key:

```env
OPENAI_API_KEY=sk-proj-abc123your-actual-key-here
```

3. Save the file

### Step 3: Run the Application
```bash
cd FleetGuard
streamlit run main.py
```

The app will automatically detect your API key from the `.env` file!

---

## ✅ How It Works

### With .env File (Recommended)
- API key is loaded automatically when you start the app
- You'll see "✅ מפתח API נטען מקובץ .env" in the sidebar
- More secure - keeps your key out of the code
- No need to enter it every time

### Without .env File (Manual Entry)
- You can still enter the API key in the sidebar
- The key is only stored for the current session
- You'll need to re-enter it each time you restart the app

---

## 🛡️ Security Best Practices

### ✅ DO:
- Keep your `.env` file in the FleetGuard folder
- Never share your `.env` file with others
- Never commit `.env` to git (already in `.gitignore`)
- Use `.env.example` as a template for others

### ❌ DON'T:
- Don't share your API key publicly
- Don't commit `.env` to version control
- Don't hardcode API keys in source files

---

## 📂 File Structure

```
FleetGuard/
├── .env              ← Your actual API key (secret)
├── .env.example      ← Template for others (safe to share)
├── .gitignore        ← Prevents .env from being committed
└── main.py           ← Loads environment variables
```

---

## 🔄 Alternative: Manual Entry

If you prefer not to use `.env`, you can still enter your API key manually:

1. Run the app: `streamlit run main.py`
2. Look for "OpenAI API Key" in the sidebar
3. Enter your key (starts with `sk-...`)
4. Use the AI Chat feature

---

## 🧪 Testing

To verify your setup works:

```bash
cd FleetGuard
python -c "from dotenv import load_dotenv; import os; load_dotenv(); key = os.getenv('OPENAI_API_KEY'); print('✓ API key loaded!' if key and key != 'your-api-key-here' else '✗ No API key found')"
```

---

## 💡 Troubleshooting

**Problem:** "No API key found" message
- **Solution:** Check that `.env` file exists and contains your key

**Problem:** AI chat not working
- **Solution:** Verify your API key is correct and has credits

**Problem:** "Invalid API key" error
- **Solution:** Make sure you copied the full key from OpenAI (starts with `sk-`)

---

**Ready to use your FleetGuard AI Chat!** 🚛✨
