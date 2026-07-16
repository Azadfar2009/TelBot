import os
import logging
from fastapi import FastAPI, Request, Response
from telegram import Update, MenuButtonCommands
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import uvicorn
from mistralai import Mistral

# ---------- تنظیمات اولیه ----------
logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN تنظیم نشده!")
if not MISTRAL_API_KEY:
    raise ValueError("MISTRAL_API_KEY تنظیم نشده!")

# ---------- راه‌اندازی FastAPI و ربات ----------
app = FastAPI()
bot_app = Application.builder().token(TELEGRAM_TOKEN).build()

# ---------- راه‌اندازی Mistral AI ----------
client = Mistral(api_key=MISTRAL_API_KEY)

# ---------- تنظیم منو در زمان شروع ----------
@app.on_event("startup")
async def startup_event():
    await bot_app.initialize()
    await bot_app.bot.set_chat_menu_button(chat_id=None, menu_button=MenuButtonCommands())
    logging.info("ربات با Mistral AI راه‌اندازی شد.")

# ---------- دستور start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"سلام {user.first_name}! 👋\n"
        "من یک ربات هوشمند هستم که با Mistral AI کار می‌کند.\n"
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

# ---------- پاسخگویی با Mistral AI ----------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    thinking_msg = await update.message.reply_text("🤔 در حال فکر کردن ...")

    try:
        chat_response = client.chat.complete(
            model="mistral-small-latest",  # یا mistral-medium-latest برای کیفیت بالاتر
            messages=[
                {
                    "role": "user",
                    "content": user_message,
                },
            ]
        )
        ai_response = chat_response.choices[0].message.content

        await thinking_msg.delete()
        await update.message.reply_text(ai_response)

    except Exception as e:
        error_msg = str(e)
        logging.error(f"خطا در Mistral: {error_msg}")
        await thinking_msg.delete()
        
        if "rate limit" in error_msg.lower():
            await update.message.reply_text("⏳ تعداد درخواست‌ها زیاد شده. لطفاً چند ثانیه صبر کن و دوباره تلاش کن.")
        else:
            await update.message.reply_text(f"❌ خطا: {error_msg[:150]}")

# ---------- ثبت دستورات ----------
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("help", help_command))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ---------- Webhook ----------
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
    return {"status": "ربات هوشمند Mistral AI فعال است!"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
