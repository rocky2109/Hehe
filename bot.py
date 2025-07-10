import os
import requests
import time
import random
import string
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

def generate_email():
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    domain = "datingso.com"
    return username, domain, f"{username}@{domain}"

def wait_for_otp(username, domain):
    for _ in range(30):  # 1 minute max wait
        inbox_url = f"https://www.1secmail.com/api/v1/?action=getMessages&login={username}&domain={domain}"
        resp = requests.get(inbox_url)
        messages = resp.json()
        if messages:
            msg_id = messages[0]['id']
            msg_url = f"https://www.1secmail.com/api/v1/?action=readMessage&login={username}&domain={domain}&id={msg_id}"
            msg_data = requests.get(msg_url).json()
            body = msg_data.get("body", "")
            import re
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
    await update.message.reply_text("📧 Generating random email address...")
    username, domain, email = generate_email()
    await update.message.reply_text("this email to login in Classplus:
<code>{email}</code>", parse_mode="HTML")
    await update.message.reply_text("⏳ Waiting for OTP...")

    otp = wait_for_otp(username, domain)
    if otp:
        await update.message.reply_text(f"✅ OTP received: <code>{otp}</code>
Verifying...", parse_mode="HTML")
        access_token = verify_classplus(email, otp)
        if access_token:
            await update.message.reply_text(f"🎉 Token generated:
<code>{access_token}</code>", parse_mode="HTML")
        else:
            await update.message.reply_text("❌ OTP verification failed. Try again.")
    else:
        await update.message.reply_text("❌ OTP not received. Try again later.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("Bot is running...")
    app.run_polling()
