import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN تنظیم نشده!")

app = Flask(__name__)

# ---------- ساخت و مقداردهی اولیه ربات ----------
bot_app = Application.builder().token(TOKEN).build()

# مقداردهی اولیه (این خط قبلاً نبود و باعث خطا می‌شد)
bot_app.initialize()

# ---------- توابع ربات ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! من با موفقیت فعال شدم.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"شما گفتید: {update.message.text}")

# ثبت دستورات
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# ---------- مسیر Webhook ----------
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        json_data = request.get_json(force=True)
        update = Update.de_json(json_data, bot_app.bot)
        
        # پردازش پیام با حلقه asyncio جدید
        asyncio.run(bot_app.process_update(update))
        
        return "OK", 200
    except Exception as e:
        logging.error(f"خطا در Webhook: {e}")
        return "Error", 500

# ---------- صفحه اصلی ----------
@app.route('/')
def home():
    return "ربات فعال است!"

# ---------- اجرا ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
