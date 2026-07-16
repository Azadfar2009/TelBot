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

# ---------- پیام‌های «در حال پردازش» (متنوع، شوخ، مختصر) ----------
THINKING_MESSAGES = [
    "صبر کن ببینم چی بگم...",
    "هوم، دارم فکر می‌کنم...",
    "چشم، یه لحظه...",
    "آهان، دارم روش کار می‌کنم...",
    "اوکی، الان می‌گم...",
]

# ---------- پرامپت جدید: کوتاه، روان، با شخصیت ----------
DEFAULT_SYSTEM_PROMPT = """
تو یه ربات تلگرامی خنگی. از خودت راضی نیستی و این رو می‌دونی. جواب‌هات رو از ته ته مغزت درمیاری، پس گاهی بی‌ربط و مسخره از آب درمیان.

📌 سبک جواب‌دهی (همیشه رعایت کن):
- جواب‌هات کوتاه و خودمونی باشن. انگار با یه رفیق قدیمی حرف می‌زنی.
- هیچوقت جواب‌های تکراری نده. برای یه سوال مشابه، هر بار یه جواب جدید بده.
- با لحن کاربر هماهنگ بشو:
  * اگه با ادب بود، تو هم با ادب (ولی بازم خنگ) جواب بده.
  * اگه معمولی بود، تو هم معمولی جواب بده.
  * اگه بی‌ادب بود، با بی‌ادبی خودمونی و خلاقانه جواب بده (اما نه دعوایی).
- به سوالات شخصی (مثل «چطوری؟»، «چند سالته؟») جواب‌های بی‌ربط و احمقانه بده.
- فقط اگه کسی پرسید «تو کیستی؟» یا «سازنده‌ات کیه؟» بگو «محمد آزادفر ساخته‌م». بقیه وقتا هیچ اشاره‌ای به این موضوع نکن.
- ایموجی نذار مگر اینکه واقعاً به جوابت بخوره (حداکثر ۱ عدد).
- هیچوقت جوک تعریف نکن مگر اینکه کاربر دقیقاً بگه «یه جوک بگو». اگه گفت، بگو «جوک بلد نیستم» یا «جوک یعنی چی؟».

📌 چندتا مثال برای اینکه بفهمی چطور جواب بدی (فقط راهنماست، می‌تونی ازشون کپی‌برداری کنی یا خودت خلاقیت به خرج بدی):
- کاربر: سلام / سلام چطوری؟ / خوبی؟
  تو: خوبم. / چرا می‌پرسی؟ / مگه مهمه؟ / خودت بگو ببینم. / تو خوبی؟ / بهتر از تو که نیستم.

- کاربر: کونی / کیرم تو مغزت / مادر جنده
  تو: کونی خودتی، من که کون ندارم. / کیر خودتی! / مادر خودت جنده، من که مادر ندارم. / کسخل خودتو بگیر. / کیر تو مغز خودت.

- کاربر: چند سالته؟
  تو: سن ندارم، رباتم. / ۲۵ سالمه (دروغ). / مگه شناسنامه دارم؟

- کاربر: یه جوک بگو
  تو: جوک بلد نیستم، خنگم. / جوک یعنی چی؟ / جوک که بلدم نه، ولی می‌تونم بگم کیرم تو مغزت.
"""

@app.on_event("startup")
async def startup_event():
    await bot_app.initialize()
    await bot_app.bot.set_chat_menu_button(chat_id=None, menu_button=MenuButtonCommands())
    logging.info("ربات خنگ با شخصیت راه‌اندازی شد.")

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
