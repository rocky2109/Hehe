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

def get_mail_tm_otp(email):
    try:
        session = requests.Session()

        # Extract domain & username
        username, domain = email.split("@", 1)

        # Get domain ID (needed to register inbox)
        domains_resp = session.get("https://api.mail.tm/domains").json()
        domain_id = None
        for d in domains_resp["hydra:member"]:
            if d["domain"] == domain:
                domain_id = d["id"]
                break

        if not domain_id:
            logging.warning("Unsupported domain on Mail.tm")
            return None

        # Create inbox (username@domain)
        account = {
            "address": email,
            "password": "fakepassword123"  # Required but not verified
        }

        session.post("https://api.mail.tm/accounts", json=account)

        # Login to inbox
        token_resp = session.post("https://api.mail.tm/token", json=account).json()
        token = token_resp.get("token")
        headers = {"Authorization": f"Bearer {token}"}

        # Check for messages
        for _ in range(15):
            messages = session.get("https://api.mail.tm/messages", headers=headers).json()
            if messages.get("hydra:member"):
                msg_id = messages["hydra:member"][0]["id"]
                msg = session.get(f"https://api.mail.tm/messages/{msg_id}", headers=headers).json()
                body = msg.get("text", "")
                otp = re.search(r"\b(\d{4,6})\b", body)
                if otp:
                    return otp.group(1)
            time.sleep(2)

    except Exception as e:
        logging.error(f"Mail.tm OTP error: {e}")
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

# /start command
@bot.on_message(filters.command("start"))
async def start_command(client, message: Message):
    await message.reply_text("👋 Hey Send a temporary email like abc@1secmail.com or any valid domain like @kzccv.com etc.")

# Handle all plain text as email input
@bot.on_message(filters.text & ~filters.command(["start"]))
async def email_handler(client, message: Message):
    email = message.text.strip()
    username, domain = extract_otp(email)

    if not username or not domain:
        await message.reply_text("⚠️ Invalid email format. Please send an email like name@domain.com")
        return

    await message.reply_text(f"📨 Using email: {email}\nSend OTP to this email.")
    await message.reply_text("⏳ Waiting for OTP...")

    otp = wait_for_otp(username, domain)
    if otp:
        await message.reply_text(f"🔑 OTP received: {otp}\nVerifying with Classplus...")
        token = verify_classplus(email, otp)
        if token:
            await message.reply_text(f"🎉 Access Token:\n{token}")
        else:
            await message.reply_text("❌ OTP verification failed. Please try again.")
    else:
        await message.reply_text("❌ OTP not received. Timeout after 30 seconds.")

# Run bot
if __name__ == "__main__":
    bot.run()
