# Setup Instructions

## ⚠️ Important: Configure Your Credentials

After cloning this repository, you MUST update the following files with your own credentials:

### 1. BTC Scanner Configuration

Edit `config/config.json`:

```json
{
  "smtp": {
    "password": "YOUR_SMTP_PASSWORD_HERE"
  },
  "telegram": {
    "bot_token": "YOUR_BOT_TOKEN_HERE",
    "chat_id": "YOUR_CHAT_ID_HERE"
  }
}
```

### 2. Gold Scanner Configuration (if using)

Edit `xauusd_scanner/config_gold.json`:

```json
{
  "telegram": {
    "bot_token": "YOUR_BOT_TOKEN_HERE",
    "chat_id": "YOUR_CHAT_ID_HERE"
  }
}
```

## 🚀 Quick Start

### On Your Linux VM:

```bash
# Clone the repository
git clone https://github.com/predeshen/telegramscalperbot.git
cd telegramscalperbot

# Update credentials
nano config/config.json
# Update telegram bot_token and chat_id

# Install dependencies
pip3 install -r requirements.txt

# Run BTC scanner
python3 main.py
```

## 📱 Getting Telegram Credentials

### Bot Token:
1. Open Telegram
2. Talk to [@BotFather](https://t.me/BotFather)
3. Send `/newbot`
4. Follow instructions
5. Copy the token

### Chat ID:
1. Talk to [@userinfobot](https://t.me/userinfobot)
2. Copy your chat ID

## 📚 Documentation

- **README.md** - Full documentation
- **QUICKSTART.md** - Quick setup guide
- **DEPLOYMENT_READY.md** - Production deployment
- **TEST_RESULTS.md** - Test results
- **ENHANCEMENTS_SUMMARY.md** - New features

## 🔒 Security Note

**NEVER commit your actual credentials to git!**

The config files in this repo contain placeholder values. Always update them with your own credentials after cloning.

## 💡 Need Help?

Check the documentation files or review the test scripts to understand how everything works.
