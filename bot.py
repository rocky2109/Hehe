import os
import re
import time
import logging
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_token_here")

# Logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# State definition
ASK_EMAIL = 0
user_email_map = {}

# Extract username and domain from email
def extract_username_domain(email):
    if "@" not in email:
        return None, None
    username, domain = email.split("@", 1)
    return username, domain

# Wait and extract OTP from email
def wait_for_otp(username, domain):
    logging.info(f"Waiting for OTP for {username}@{domain}")
    inbox_url = f"https://www.1secmail.com/api/v1/?action=getMessages&login={username}&domain={domain}"

    for attempt in range(15):
        try:
            resp = requests.get(inbox_url)
            messages = resp.json()
            if messages:
                msg_id = messages[0]["id"]
                msg_url = f"https://www.1secmail.com/api/v1/?action=readMessage&login={username}&domain={domain}&id={msg_id}"
                msg_data = requests.get(msg_url).json()
                body = msg_data.get("body", "")
                otp_match = re.search(r"\b(\d{4,6})\b", body)
                if otp_match:
                    return otp_match.group(1)
        except Exception as e:
            logging.error(f"Error fetching OTP: {e}")
        time.sleep(2)

    return None

# Verify OTP with Classplus
def verify_classplus(email, otp):
    payload = {
        "email": email,
        "otp": otp,
        "countryCode": "+91",
        "userType": 0
    }
    headers = {
        "x-application-id": "classplus",
        "content-type": "application/json"
    }

    try:
        r = requests.post("https://api.classplusapp.com/v2/customer/otp/verify", json=payload, headers=headers)
        if r.status_code == 200:
            return r.json().get("data", {}).get("accessToken")
    except Exception as e:
        logging.error(f"Classplus verification error: {e}")
    return None

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome! Please send a temporary email address (e.g. `abc@1secmail.com`, `@kzccv.com`, etc.):",
        parse_mode="Markdown"
    )
    return ASK_EMAIL

# Get email and process OTP
async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    username, domain = extract_username_domain(email)

    if not username or not domain:
        await update.message.reply_text("⚠️ Invalid email format. Please send a valid email like `name@domain.com`.", parse_mode="Markdown")
        return ASK_EMAIL

    user_email_map[update.effective_user.id] = (email, username, domain)

    await update.message.reply_text(f"✅ Email set: `{email}`\nPlease send the OTP to this email via Classplus.", parse_mode="Markdown")
    await update.message.reply_text("⏳ Waiting for OTP... (Timeout: 30 sec)")

    otp = wait_for_otp(username, domain)
    if otp:
        await update.message.reply_text(f"🔑 OTP received: `{otp}`\n🛡 Verifying with Classplus...", parse_mode="Markdown")
        token = verify_classplus(email, otp)
        if token:
            await update.message.reply_text(f"🎉 Access Token:\n`{token}`", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Verification failed. The OTP might be wrong or expired.")
    else:
        await update.message.reply_text("❌ OTP not received in time. Please try again.")

    return ConversationHandler.END

# /cancel command
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Process cancelled. Use /start to begin again.")
    return ConversationHandler.END

# Start bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    logging.info("🤖 Bot is running...")
    app.run_polling()
