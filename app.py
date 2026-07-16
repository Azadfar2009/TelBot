import os
import logging
from fastapi import FastAPI, Request, Response
from telegram import Update, MenuButtonCommands
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import uvicorn
import google.generativeai as genai

# ---------- تنظیمات اولیه ----------
logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN تنظیم نشده!")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY تنظیم نشده!")

# ---------- راه‌اندازی FastAPI و ربات ----------
app = FastAPI()
bot_app = Application.builder().token(TELEGRAM_TOKEN).build()

# ---------- راه‌اندازی Gemini ----------
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")  # مدل رایگان و سریع

# ---------- تنظیم منو در زمان شروع ----------
@app.on_event("startup")
async def startup_event():
    await bot_app.initialize()
    # این خط باعث می‌شود دکمه‌ی منو در تلگرام ظاهر شود
    await bot_app.bot.set_chat_menu_button(chat_id=None, menu_button=MenuButtonCommands())
    logging.info("ربات با منو و Gemini راه‌اندازی شد.")

# ---------- دستور start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"سلام {user.first_name}! 👋\n"
        "من یک ربات هوشمند هستم که با Gemini کار می‌کند.\n"
        "هر سوالی داری، بپرس!"
    )

# ---------- دستور help ----------
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **راهنما**\n"
        "/start - شروع مجدد\n"
        "/help - نمایش این پیام\n"
        "هر سوال دیگری را مستقیم بپرسید."
    )

# ---------- پاسخگویی با Gemini ----------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    thinking_msg = await update.message.reply_text("🤔 در حال فکر کردن ...")

    try:
        response = model.generate_content(user_message)
        ai_response = response.text

        await thinking_msg.delete()
        await update.message.reply_text(ai_response)

    except Exception as e:
        logging.error(f"خطا در Gemini: {e}")
        await thinking_msg.delete()
        await update.message.reply_text("❌ خطایی رخ داد. لطفاً دوباره تلاش کن.")

# ---------- ثبت دستورات ----------
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("help", help_command))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ---------- Webhook (همان کد قبلی) ----------
@app.post("/webhook")
async def webhook(request: Request):
    try:
        json_data = await request.json()
        update = Update.de_json(json_data, bot_app.bot)
        await bot_app.process_update(update)
        return Response(content="OK", status_code=200)
    except Exception as e:
        logging.error(f"خطا در Webhook: {e}")
        return Response(content="Error", status_code=500)

@app.get("/")
async def home():
    return {"status": "ربات هوشمند Gemini فعال است!"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
