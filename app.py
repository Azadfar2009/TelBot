import os
import logging
import json
from flask import Flask, request, Response
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN تنظیم نشده!")

app = Flask(__name__)

# ---------- ساخت ربات ----------
bot_app = Application.builder().token(TOKEN).build()

# ---------- توابع ربات (حالت معمولی) ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! من با Webhook کار می‌کنم و خوشحالم که فعال هستم!")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"شما گفتید: {update.message.text}")

# ثبت دستورات
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# ---------- مسیر Webhook (بدون async) ----------
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # دریافت اطلاعات از تلگرام
        json_data = request.get_json()
        if not json_data:
            return "Invalid data", 400

        # تبدیل به آبجکت Update
        update = Update.de_json(json_data, bot_app.bot)
        
        # پردازش پیام (اجرای دستی تابع async)
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot_app.process_update(update))
        loop.close()
        
        return "OK", 200
    except Exception as e:
        logging.error(f"خطا در Webhook: {e}")
        return "Error", 500

# ---------- صفحه اصلی ----------
@app.route('/')
def home():
    return "ربات فعال است! Webhook در مسیر /webhook قرار دارد."

# ---------- اجرا ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
