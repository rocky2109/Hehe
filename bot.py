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

import requests
import re
import time
import logging

def wait_for_otp_1secmail(username: str, domain: str, retries: int = 15, delay: int = 2) -> str | None:
    import requests, re, time, logging
    logging.info(f"📬 Waiting for OTP at {username}@{domain}")

    inbox_url = f"https://www.1secmail.com/api/v1/?action=getMessages&login={username}&domain={domain}"

    for attempt in range(retries):
        try:
            response = requests.get(inbox_url)
            if response.status_code != 200:
                logging.warning(f"⚠️ Inbox fetch failed (HTTP {response.status_code})")
                time.sleep(delay)
                continue

            try:
                messages = response.json()
            except Exception:
                logging.error(f"❌ Invalid JSON in inbox: {response.text}")
                time.sleep(delay)
                continue

            if messages:
                msg_id = messages[0]["id"]
                msg_url = f"https://www.1secmail.com/api/v1/?action=readMessage&login={username}&domain={domain}&id={msg_id}"
                msg_data = requests.get(msg_url).json()

                body = msg_data.get("body", "") or msg_data.get("textBody", "")
                otp_match = re.search(r"\b\d{4,6}\b", body)

                if otp_match:
                    otp = otp_match.group(0)
                    logging.info(f"✅ OTP found: {otp}")
                    return otp
                else:
                    logging.warning("📭 Message received but no OTP found.")

        except Exception as e:
            logging.error(f"OTP error: {e}")

        time.sleep(delay)

    logging.warning("⌛ Timed out waiting for OTP.")
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
