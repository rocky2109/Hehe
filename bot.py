import os
import re
import time
import logging
import requests
from pyrogram import Client, filters
from pyrogram.types import Message

# Load BOT_TOKEN from Render environment
BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = int(os.environ.get("API_ID", 12345))       # Add real value in Render
API_HASH = os.environ.get("API_HASH", "abc123")     # Add real value in Render

# Logging
logging.basicConfig(level=logging.INFO)

# Bot setup
bot = Client(
    name="classplusbot",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH
)

# OTP extract function
def extract_otp(email):
    if "@" not in email:
        return None, None
    return email.split("@", 1)

def wait_for_otp(username, domain):
    logging.info(f"Waiting for OTP for {username}@{domain}")
    inbox_url = f"https://www.1secmail.com/api/v1/?action=getMessages&login={username}&domain={domain}"
    
    for _ in range(15):
        try:
            messages = requests.get(inbox_url).json()
            if messages:
                msg_id = messages[0]["id"]
                msg_data = requests.get(
                    f"https://www.1secmail.com/api/v1/?action=readMessage&login={username}&domain={domain}&id={msg_id}"
                ).json()
                otp_match = re.search(r"\b(\d{4,6})\b", msg_data.get("body", ""))
                if otp_match:
                    return otp_match.group(1)
        except Exception as e:
            logging.error(f"OTP error: {e}")
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

    try:
        r = requests.post("https://api.classplusapp.com/v2/customer/otp/verify", json=payload, headers=headers)
        if r.status_code == 200:
            return r.json().get("data", {}).get("accessToken")
    except Exception as e:
        logging.error(f"Classplus verification error: {e}")
    return None

# Start command
@bot.on_message(filters.command("start"))
async def start_command(client, message: Message):
    await message.reply_text("👋 Welcome! Send a temporary email like `abc@1secmail.com`, `@kzccv.com`, etc.", parse_mode="markdown")

# Handle all plain text as email
@bot.on_message(filters.text & ~filters.command)
async def email_handler(client, message: Message):
    email = message.text.strip()
    username, domain = extract_otp(email)

    if not username or not domain:
        await message.reply_text("❌ Invalid email. Format must be: `name@domain.com`", parse_mode="markdown")
        return

    await message.reply_text(f"📨 Using email: `{email}`\nSend OTP to this email.", parse_mode="markdown")
    await message.reply_text("⏳ Waiting for OTP...")

    otp = wait_for_otp(username, domain)
    if otp:
        await message.reply_text(f"🔑 OTP received: `{otp}`\nVerifying with Classplus...", parse_mode="markdown")
        token = verify_classplus(email, otp)
        if token:
            await message.reply_text(f"🎉 Access Token:\n`{token}`", parse_mode="markdown")
        else:
            await message.reply_text("❌ OTP verification failed.")
    else:
        await message.reply_text("❌ OTP not received. Try again later.")

# Run bot
if __name__ == "__main__":
    bot.run()
