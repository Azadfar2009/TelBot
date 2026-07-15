import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN تنظیم نشده!")

app = Flask(__name__)

# ---------- ساخت ربات ----------
bot_app = Application.builder().token(TOKEN).build()

# ---------- توابع ربات ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! من با روش Webhook کار می‌کنم.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"شما گفتید: {update.message.text}")

# ثبت دستورات
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# ---------- مسیر Webhook برای تلگرام ----------
@app.route('/webhook', methods=['POST'])
async def webhook():
    data = request.get_json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return 'OK', 200

# ---------- صفحه اصلی برای بررسی زنده بودن ----------
@app.route('/')
def home():
    return "ربات فعال است!"

# ---------- تنظیم Webhook در استارت ----------
@app.before_first_request
def set_webhook():
    webhook_url = "https://azadsoftbot.onrender.com/webhook"
    bot_app.bot.set_webhook(url=webhook_url)
    logging.info(f"Webhook با موفقیت روی {webhook_url} تنظیم شد.")

# ---------- اجرای Flask ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
