import os
import logging
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- تنظات اولیه ---
logging.basicConfig(level=logging.INFO)
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("متغیر محیطی TELEGRAM_TOKEN تنظیم نشده!")

# --- فلاسک برای اشغال پورت (برای اینکه Render خاموشش نکنه) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "ربات من زنده است!"

@app.route('/health')
def health():
    return "OK"

# --- توابع ربات (مغز ربات) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! من یه ربات سادم که با روش Serverless کار میکنه.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"شما گفتید: {update.message.text}")

# --- تابع اصلی برای اجرای ربات ---
def run_bot():
    # اپلیکیشن ربات رو میسازیم
    bot_app = Application.builder().token(TOKEN).build()
    
    # دستورات رو ثبت میکنیم
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    # ربات رو با روش Polling (همون روش قدیمی) اجرا میکنیم
    print("ربات شروع به کار کرد...")
    bot_app.run_polling()

# --- نقطه ورود برنامه ---
if __name__ == "__main__":
    # ربات رو در یک نخ (Thread) جداگانه اجرا کن تا با فلاسک تداخل نداشته باشه
    thread = threading.Thread(target=run_bot)
    thread.start()
    
    # فلاسک رو روی پورتی که Render به ما میده اجرا کن تا سرویس فعال نمونه
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
