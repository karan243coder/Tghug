# 🤖 Advanced Telegram AI Image Editor Bot

**FREE AI Image Editing with Professional Progress Display**

---

## ✨ Key Features

### 📊 Advanced Progress Display
- **13 Processing Stages** with visual indicators
- **Color-coded progress bar** (🟥 → 🟨 → 🟦 → 🟩)
- **Real-time checklist** showing completed/current/pending steps
- **Multiple timers** (total time + stage time)
- **API call stats** (calls, retries)

### 🛡️ Flood Wait Protection
- **Auto-detects** Telegram rate limits
- **Waits automatically** when needed
- **Retries up to 5 times** with backoff
- **Never crashes** from flood waits

### 🔘 Proper Button Handling
- **All 12 buttons** work correctly
- **Immediate response** (no loading spinner)
- **State management** for proper flow
- **Error recovery** for invalid states

---

## 🚀 Quick Start

### 1. Get Tokens (FREE!)

**Telegram Bot Token:**
1. Open Telegram → Search `@BotFather`
2. Send `/newbot`
3. Follow instructions
4. **Copy the token!**

**Hugging Face Token (FREE):**
1. Go to https://huggingface.co/join
2. Create account (FREE)
3. Go to https://huggingface.co/settings/tokens
4. Create new token (Read permission)
5. **Copy the token!**

### 2. Deploy to Koyeb (FREE!)

1. Go to https://app.koyeb.com/signup
2. Create account (FREE)
3. Create Secrets:
   - `TELEGRAM_BOT_TOKEN` = your bot token
   - `HUGGINGFACE_TOKEN` = your HF token
4. Create App → Docker
5. Instance: **Nano** (512MB RAM - FREE!)
6. Deploy!

### 3. Use the Bot!

1. Find your bot on Telegram
2. Send `/start`
3. Send a **photo**
4. Choose **preset** or **custom prompt**
5. Watch **real-time progress**!
6. Get **edited image**!

---

## 📊 Progress Display Example

```
╔══════════════════════════════════════╗
║    🤖 AI IMAGE EDITOR - PROGRESS    ║
╚══════════════════════════════════════╝

📊 STATUS: 🤖 AI Processing
📋 DETAIL: AI is editing your image

⏳ PROGRESS: 65%
🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩⬜⬜⬜⬜⬜
📍 STEP: 7/9

⏱️ TOTAL TIME: 45s
⏱️ STAGE TIME: 12s

📝 PROCESS CHECKLIST:
✅ 📸 Image Received
✅ 🔍 Validating Image
✅ ✍️ Waiting for Prompt
✅ 📝 Processing Prompt
✅ 📦 Preparing Request
✅ ☁️ Uploading Image
➡️ 🤖 AI Processing ← CURRENT
⬜ ⬇️ Downloading Result
⬜ 🎨 Post Processing
```

---

## 🎯 Available Presets

| Preset | Description |
|--------|-------------|
| 🌅 Background Change | Change to sunset beach |
| 🎨 Artistic Style | Oil painting effect |
| 😎 Add Accessories | Add sunglasses |
| ✍️ Custom Prompt | Write your own |

---

## 💡 Custom Prompt Examples

- "Change background to mountain view"
- "Make it look like a superhero"
- "Add a cowboy hat"
- "Change hair to curly red"
- "Transform into anime character"
- "Make it professional for LinkedIn"

**Pro Tip:** Add "keep face same" for best results!

---

## 🔧 Commands

| Command | Description |
|---------|-------------|
| /start | Start the bot |
| /help | Show help guide |
| /cancel | Cancel operation |
| /status | Check processing status |

---

## ⚠️ Important Notes

### Face Consistency
- Use **front-facing photos**
- Ensure **good lighting**
- **Face clearly visible**
- Add **"keep face same"** in prompt

### Processing Time
- **30-120 seconds** typical
- First time may be slower
- Free API may have delays

### Free Tier Limits
- **Hugging Face:** Free with rate limits
- **Koyeb:** 512MB RAM free tier
- **Bot:** Unlimited users!

---

## 🛡️ Flood Wait Protection

The bot handles Telegram rate limits automatically:

1. **Detects** RetryAfter errors
2. **Waits** required time
3. **Retries** the operation
4. **Continues** normally

**Your bot will NEVER crash from rate limits!**

---

## 📁 Project Structure

```
telegram-image-editor/
├── bot.py              # Main bot code (advanced)
├── requirements.txt    # Python dependencies
├── Dockerfile         # Koyeb deployment
├── koyeb.yaml         # Koyeb config
├── .env.example       # Token template
├── FEATURES.md        # Feature documentation
└── README.md          # This file
```

---

## 🎓 Technical Details

### Progress System
- **13 stages** tracked
- **Visual progress bar** with colors
- **Checklist** with icons
- **Multiple timers**

### Flood Protection
- **Rate limiting** per action
- **RetryAfter** handling
- **Exponential backoff**
- **5 max retries**

### Button System
- **12 unique buttons**
- **Immediate callback** response
- **State validation**
- **Error recovery**

### Memory Optimization
- **In-memory processing**
- **Auto cleanup** of old states
- **BytesIO streams**
- **Minimal footprint**

---

## 🐛 Troubleshooting

### Bot not responding?
- Wait 30 seconds
- Try /cancel
- Check Koyeb logs

### Processing failed?
- Try again in 5 minutes
- Use different photo
- Simpler prompt

### Face changed?
- Add "keep face same" in prompt
- Use front-facing photo
- Better lighting needed

### Rate limited?
- Bot handles automatically
- Just wait a moment
- Will retry on its own

---

## 📞 Support

1. Check this README
2. Try /help in bot
3. Check Koyeb logs
4. Wait and retry

---

## 📜 License

MIT License - Free to use!

---

## 🎉 Ready to Deploy!

Everything is set up. Just:
1. Get your tokens
2. Deploy to Koyeb
3. Start using!

**Enjoy your AI Image Editor! 🚀**

---

Made with ❤️ | Bilkul FREE! | Advanced Progress | Flood Protected
