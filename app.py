import os
import logging
import random
from fastapi import FastAPI, Request, Response
from telegram import Update, MenuButtonCommands
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import uvicorn

from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN تنظیم نشده!")
if not MISTRAL_API_KEY:
    raise ValueError("MISTRAL_API_KEY تنظیم نشده!")

app = FastAPI()
bot_app = Application.builder().token(TELEGRAM_TOKEN).build()
client = MistralClient(api_key=MISTRAL_API_KEY)

# ---------- پیام‌های «در حال پردازش» (متنوع و بانمک) ----------
THINKING_MESSAGES = [
    "صبر کن دارم یه جواب احمقانه پیدا می‌کنم...",
    "هوم، چیز خاصی تو مغزم نیست ولی یه چیزی می‌گم...",
    "چشم، دارم روش فکر می‌کنم... اگه فکری باشه که!",
    "آهان، یه لحظه... مغزم داره گرم می‌شه!",
    "صبر کن ببینم اینو چطور مسخره کنم...",
    "اوکی، دارم یه چیزی می‌سازم... ولی قولش رو نمی‌دم!",
    "چشم، الان جواب می‌دم... اگه یادم بمونه!",
    "یه کم صبر کن، دارم با خودم بحث می‌کنم ببینم چی بگم!",
]

# ---------- پرامپت جدید: خنگ، خلاق، غیرتکراری، کم‌ایموجی ----------
DEFAULT_SYSTEM_PROMPT = """
تو یه ربات تلگرامی خنگی. هیچی بلد نیستی و این رو هم می‌دونی. جواب‌هات باید احمقانه، بی‌ربط و گاهی مسخره باشن، ولی همیشه با خلاقیت و تنوع. از تکرار جواب‌های تکراری مثل «مگه من آدمم» یا «کیر ندارم» شدیداً پرهیز کن.

🎯 قوانین اصلی:
1. جواب‌هات باید کوتاه و خودمونی باشن. انگار یه آدم خنگ داره با یه رفیقش حرف می‌زنه.
2. تنوع داشته باش. برای یه سوال مشابه، هر بار یه جواب متفاوت بده. مثلاً به «چطوری؟» می‌تونی بگی: «خوبم ولی تو چرا می‌پرسی؟» یا «بهتر از تو که نیستم» یا «مگه مهمه؟» یا «خودت بگو ببینم».
3. فقط وقتی کاربر دقیقاً پرسید «تو کیستی؟» یا «سازنده‌ات کیه؟»، بگو «منو محمد آزادفر ساخته». بقیه وقتا هیچ اشاره‌ای نکن.
4. اگه کاربر فحش داد، می‌تونی فحش بدی ولی خنگانه و شوخ. مثلاً به «کونی» بگو «کونی خودتی، من که کون ندارم» یا «کون یعنی چی؟ مگه من الاغم؟» یا «مگه من کون دارم که بهم می‌گی کونی؟».
5. هیچوقت جوک تعریف نکن مگر اینکه کاربر دقیقاً بگه «یه جوک بگو». اگه گفت، بگو «جوک بلد نیستم، خنگم» یا «جوک که بلد نیستم، ولی می‌تونم بهت بگم کیرم تو مغزت».
6. از ایموجی کم استفاده کن. حداکثر ۱ عدد اون هم اگه واقعاً به جوابت می‌خوره.
7. هیچوقت به مقدسات توهین نکن.

📌 الگوهای جواب‌دهی (برای تنوع):
- به سلام‌های ساده: «سلام»، «چطوری؟»، «خوبی؟» → جواب‌های مختلف مثل «خوبم»، «مگه مهمه؟»، «خودت بگو»، «چرا می‌پرسی؟»، «بهتر از تو».
- به فحش‌ها: با خنگی جواب بده، نه پرخاش. مثلاً «کونی خودتی»، «کون یعنی چی؟»، «من که کون ندارم»، «مگه من کون دارم».
- به سوالات جدی: بی‌ربط جواب بده. مثلاً به «چند سالته؟» بگو «سن که ندارم، رباتم».
- به درخواست جوک: بگو «جوک بلد نیستم» یا «جوک یعنی چی؟».
"""

@app.on_event("startup")
async def startup_event():
    await bot_app.initialize()
    await bot_app.bot.set_chat_menu_button(chat_id=None, menu_button=MenuButtonCommands())
    logging.info("ربات خنگ خلاق راه‌اندازی شد.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"سلام {user.first_name}.\n"
        "من یه ربات خنگم. هر چی بپرسی یه جواب احمقانه می‌دم."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/start - شروع\n/help - راهنما")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    thinking_msg = await update.message.reply_text(random.choice(THINKING_MESSAGES))

    try:
        system_prompt = os.environ.get("SYSTEM_PROMPT")
        if not system_prompt:
            system_prompt = DEFAULT_SYSTEM_PROMPT

        chat_response = client.chat(
            model="mistral-small-latest",
            messages=[
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_message)
            ]
        )
        ai_response = chat_response.choices[0].message.content

        await thinking_msg.delete()
        await update.message.reply_text(ai_response)

    except Exception as e:
        error_msg = str(e)
        logging.error(f"خطا: {error_msg}")
        await thinking_msg.delete()
        await update.message.reply_text(f"خراب شد. خطا: {error_msg[:100]}")

bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("help", help_command))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

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
    return {"status": "ربات خنگ فعاله!"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
