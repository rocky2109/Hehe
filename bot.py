import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler

# States
ASK_EMAIL, ASK_OTP = range(2)

# Store temporary user data
user_data = {}

# Classplus API endpoints
SEND_OTP_URL = "https://api.classplusapp.com/v2/customer/otp/login"
VERIFY_OTP_URL = "https://api.classplusapp.com/v2/customer/otp/verify"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome! Please send your email to begin token generation.")
    return ASK_EMAIL

async def ask_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text
    user_id = update.effective_user.id
    user_data[user_id] = {"email": email}

    # Send OTP
    payload = {
        "email": email,
        "countryCode": "+91",
        "userType": 0
    }
    headers = {
        "x-application-id": "classplus",
        "content-type": "application/json"
    }
    response = requests.post(SEND_OTP_URL, json=payload, headers=headers)
    if response.status_code == 200:
        await update.message.reply_text("📩 OTP sent to your email. Please enter the OTP.")
        return ASK_OTP
    else:
        await update.message.reply_text("❌ Failed to send OTP. Please try again.")
        return ConversationHandler.END

async def ask_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp = update.message.text
    user_id = update.effective_user.id
    email = user_data.get(user_id, {}).get("email")

    if not email:
        await update.message.reply_text("⚠️ Session expired. Please restart with /start")
        return ConversationHandler.END

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
    response = requests.post(VERIFY_OTP_URL, json=payload, headers=headers)
    if response.status_code == 200:
        data = response.json()
        token = data.get("data", {}).get("accessToken")
        if token:
            await update.message.reply_text(f"✅ Token generated successfully:\n\n<code>{token}</code>", parse_mode="HTML")
        else:
            await update.message.reply_text("❌ Failed to extract token.")
    else:
        await update.message.reply_text("❌ OTP verification failed.")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Process cancelled.")
    return ConversationHandler.END

if __name__ == '__main__':
    import dotenv
    dotenv.load_dotenv()

    TOKEN = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_email)],
            ASK_OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_otp)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(conv_handler)
    print("Bot is running...")
    app.run_polling()