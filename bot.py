import os
import requests
import time
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

EMAIL = "sawodi6262"
DOMAIN = "datingso.com"
FULL_EMAIL = f"{EMAIL}@{DOMAIN}"

def wait_for_otp():
    for _ in range(30):
        inbox_url = f"https://www.1secmail.com/api/v1/?action=getMessages&login={EMAIL}&domain={DOMAIN}"
        resp = requests.get(inbox_url)
        messages = resp.json()
        if messages:
            msg_id = messages[0]["id"]
            msg_url = f"https://www.1secmail.com/api/v1/?action=readMessage&login={EMAIL}&domain={DOMAIN}&id={msg_id}"
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
    await update.message.reply_text(f"📧 Use this fixed email in Classplus:\n<code>{FULL_EMAIL}</code>", parse_mode="HTML")
    await update.message.reply_text("⏳ Waiting for OTP to arrive...")

    otp = wait_for_otp()
    if otp:
        await update.message.reply_text(f"✅ OTP received: <code>{otp}</code>\nVerifying...", parse_mode="HTML")
        token = verify_classplus(FULL_EMAIL, otp)
        if token:
            await update.message.reply_text(f"🎉 Token:\n<code>{token}</code>", parse_mode="HTML")
        else:
            await update.message.reply_text("❌ OTP verification failed.")
    else:
        await update.message.reply_text("❌ OTP not received. Try again later.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("Bot running...")
    app.run_polling()
    
