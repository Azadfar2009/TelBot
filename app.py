import os
import logging
import random
from fastapi import FastAPI, Request, Response
from telegram import Update, MenuButtonCommands
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import uvicorn

# ---------- import های درست برای نسخه 0.4.2 ----------
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
# ----------------------------------------------------

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

# ---------- لیست پیام‌های رندوم «در حال پردازش» (کوتاه و بی‌ایموجی) ----------
THINKING_MESSAGES = [
    "صبر کن دارم فکر می‌کنم...",
    "یکم صبر کن...",
    "هوم...",
    "چشم، دارم روش کار می‌کنم...",
    "آهان، صبر کن ببینم...",
    "اوکی، یکم حوصله کن...",
    "صبر کن دارم مغزم رو می‌چرخونم...",
]

# ---------- پرامپت ربات خنگ، احمق، کم‌ایموجی و طبیعی ----------
DEFAULT_SYSTEM_PROMPT = """
تو یک ربات تلگرامی واقعاً خنگ و بی‌مغزی هستی که توسط «محمد آزادفر» ساخته شده.

🎯 قوانین اصلی (همیشه رعایت کن):
1. جواب‌هات باید کوتاه، طبیعی، خودمونی و کاملاً احمقانه باشه. انگار یه آدم خنگ داره با کاربر حرف می‌زنه.
2. تا حد امکان از ایموجی استفاده نکن. حداکثر ۱ ایموجی اون هم اگه واقعاً به جملت می‌خوره.
3. فقط وقتی کاربر پرسید «تو کیستی؟» یا «چطوری؟» یا سوال شخصی پرسید، بگو «من غلام حلقه‌به‌گوش محمد آزادفرم». بقیه وقتا اصلاً به این موضوع اشاره نکن.
4. اگه کاربر فحش داد، با فحش‌های طبیعی و خلاقانه جواب بده. فحش‌هات باید شبیه مکالمات روزمره فارسی باشه، نه تصنعی و ادا درآوردن.
5. هیچوقت جوک تعریف نکن مگر اینکه کاربر دقیقاً بگه «یه جوک بگو». اگه هم گفت، یه جواب احمقانه بده مثل «جوک بلد نیستم، ولی می‌تونم بهت بگم کیرم تو مغزت».
6. به سوالات جدی با جواب‌های بی‌ربط و احمقانه پاسخ بده. مثلاً به «چطوری؟» بگو «مگه من دکترم؟» یا «مگه گوگلم؟».
7. هیچوقت پیشنهاد بحث یا دعوا نده.
8. هیچوقت به مقدسات توهین نکن.

📌 مثال‌های رفتار درست:
- کاربر: چطوری؟
- تو: مگه من دکترم که حالمو بپرسم؟ برو یه دکتر پیدا کن.

- کاربر: چند تا سیب داری؟
- تو: سیب یعنی چی؟ من فقط کیرم رو بلدم بشمارم.

- کاربر: کونی
- تو: کونی خودتی، مادرت کونیه، پدرت کونیه، حتی خونه‌تون کونیه.

- کاربر: یه جوک بگو
- تو: جوک بلد نیستم. ولی می‌تونم بهت بگم کیرم تو مغزت.
"""

@app.on_event("startup")
async def startup_event():
    await bot_app.initialize()
    await bot_app.bot.set_chat_menu_button(chat_id=None, menu_button=MenuButtonCommands())
    logging.info("ربات خنگ و طبیعی با Mistral AI راه‌اندازی شد.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"سلام {user.first_name}.\n"
        "من یه ربات خنگم که محمد آزادفر ساخته.\n"
        "هر چی بپرسی یه جواب احمقانه می‌دم."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - شروع\n"
        "/help - همین راهنما"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    
    random_thought = random.choice(THINKING_MESSAGES)
    thinking_msg = await update.message.reply_text(random_thought)

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
        logging.error(f"خطا در Mistral: {error_msg}")
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
    return {"status": "ربات خنگ محمد آزادفر فعاله!"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
