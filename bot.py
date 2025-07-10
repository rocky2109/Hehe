import os
import re
import time
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# States
ASK_EMAIL = 0
user_email_map = {}

def extract_username_domain(email):
    if "@" not in email:
        return None, None
    parts = email.split("@")
    return parts[0], parts[1]

def wait_for_otp(username, domain):
    for _ in range(30):
        inbox_url = f"https://www.1secmail.com/api/v1/?action=getMessages&login={username}&domain={domain}"
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
        time.sleep(2)
    return None

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
    r = requests.post("https://api.classplusapp.com/v2/customer/otp/verify", json=payload, headers=headers)
    if r.status_code == 200:
        return r.json().get("data", {}).get("accessToken")
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Send your temp email (e.g. something@1secmail.com or @kzccv.com or @datingso.com):")
    return ASK_EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    username, domain = extract_username_domain(email)
    if not username or not domain:
        await update.message.reply_text("⚠️ Invalid email format. Please send a valid email like name@domain.com")
        return ASK_EMAIL

    user_email_map[update.effective_user.id] = (email, username, domain)

    await update.message.reply_text(f"✅ Using email: <code>{email}</code>\nNow send OTP to this email from Classplus.", parse_mode="HTML")
    await update.message.reply_text("⏳ Waiting for OTP...")

    otp = wait_for_otp(username, domain)
    if otp:
        await update.message.reply_text(f"🔑 OTP received: <code>{otp}</code>\nVerifying...", parse_mode="HTML")
        token = verify_classplus(email, otp)
        if token:
            await update.message.reply_text(f"🎉 Token:\n<code>{token}</code>", parse_mode="HTML")
        else:
            await update.message.reply_text("❌ OTP verification failed.")
    else:
        await update.message.reply_text("❌ OTP not received. Try again.")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelled.")
    return ConversationHandler.END

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv)
    print("Bot is running...")
    app.run_polling()
