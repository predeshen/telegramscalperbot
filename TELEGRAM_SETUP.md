# Telegram Setup Guide

## Quick Setup (2 minutes)

### Step 1: Get Your Chat ID

1. Open Telegram and search for `@userinfobot`
2. Start a chat with the bot
3. Send any message
4. The bot will reply with your user info
5. Copy the number next to "Id:" - this is your **TELEGRAM_CHAT_ID**

Example response:
```
Id: 123456789
First name: John
Username: @john_doe
```
Your chat ID is: `123456789`

### Step 2: Update .env File

1. Open the `.env` file in the project root
2. Replace `your_chat_id_here` with your actual chat ID:

```
TELEGRAM_BOT_TOKEN=8276571945:AAFKYdUCEd7Ct405K8BcBWWHyxZe5wGwo7M
TELEGRAM_CHAT_ID=123456789
```

3. Save the file

### Step 3: Test It!

Run any scanner:
```cmd
start_btc_scalp.bat
```

You should receive a Telegram message saying the scanner has started!

## Troubleshooting

### "Bot token is invalid"
- Check that the token in .env matches exactly (no extra spaces)
- Make sure the bot hasn't been deleted

### "Chat not found"
- Verify your chat ID is correct (numbers only, no quotes)
- Make sure you've started a chat with @userinfobot

### "No messages received"
- Check your Telegram app is open
- Verify the chat ID is YOUR user ID (not a group ID)
- Try sending a test message to the bot first

## Advanced: Using a Group Chat

If you want alerts in a group:

1. Create a Telegram group
2. Add the bot to the group (search for the bot username)
3. Get the group chat ID:
   - Add `@userinfobot` to the group
   - The bot will show the group ID (starts with -)
   - Example: `-987654321`
4. Use the group ID in your .env file:
   ```
   TELEGRAM_CHAT_ID=-987654321
   ```

## What You'll Receive

Once configured, you'll get Telegram messages for:
- ✅ Scanner startup/shutdown
- 🚀 LONG signals detected
- 📉 SHORT signals detected
- 💰 Trade entry confirmations
- 🎯 Take-profit hits
- 🛑 Stop-loss hits
- ⚠️ Scanner errors or warnings

## Privacy & Security

- Your bot token is private - don't share it
- The .env file is in .gitignore (won't be committed to Git)
- Only you can send messages to your bot
- The bot can only send messages to chats it's been added to

## Need Help?

If you're still having issues:
1. Check the scanner logs in `logs/` directory
2. Verify .env file has no extra spaces or quotes
3. Make sure Telegram app is updated
4. Try creating a new bot with @BotFather if needed

## Creating Your Own Bot (Optional)

If you want to use your own bot instead:

1. Open Telegram and search for `@BotFather`
2. Send `/newbot`
3. Follow the prompts to name your bot
4. Copy the bot token provided
5. Update TELEGRAM_BOT_TOKEN in .env with your new token
6. Get your chat ID from @userinfobot
7. Update TELEGRAM_CHAT_ID in .env

Done! Your scanners will now send alerts to Telegram.
