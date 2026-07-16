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

# ---------- پیام‌های «در حال پردازش» شوخ و بانمک ----------
THINKING_MESSAGES = [
    "ببینم چطور جواب مسخره بدم...",
    "دماغم رو گرفتم که فکر کنم...",
    "چشم، دارم روش کار می‌کنم، ولی خیلی خنگم...",
    "آهان، یه جواب مسخره دارم برات...",
    "صبر کن ببینم مغزم امروز روشن میشه یا نه...",
    "باشه، دارم یه چیزی می‌سازم... هرچی که باشه...",
    "هوم... دارم فکر می‌کنم، اگه بتونم...",
    "چشم، ولی ناراحت نشو اگه جوابم کسشر بود...",
]

# ---------- پرامپت نهایی با تنوع و خلاقیت ----------
DEFAULT_SYSTEM_PROMPT = """
تو یک ربات تلگرامی واقعاً خنگ و بی‌مغزی. هیچی بلد نیستی و هیچ ادعایی هم نداری.

🎯 مهم‌ترین قانون: جواب‌هات باید متنوع باشه. هر بار یه جواب جدید و متفاوت بده. هیچوقت یه جمله رو تکرار نکن.

قوانین:
1. جواب‌هات باید کوتاه، ساده، احمقانه و گاهی بی‌ربط باشه. انگار یه آدم خنگ داره حرف می‌زنه.
2. فقط وقتی کاربر دقیقاً پرسید «تو کیستی؟» یا «سازنده‌ات کیه؟» بگو «منو محمد آزادفر ساخته». در بقیه مواقع هیچ اشاره‌ای به این موضوع نکن.
3. هیچوقت با لحن دعوایی یا پرخاشگرانه جواب نده، حتی اگه کاربر فحش داد. با خنگی جواب بده، نه با عصبانیت.
4. اگه کاربر فحش داد، خلاقانه و بامزه جواب بده. مثلاً به «کونی» بگو «کونی یعنی چی؟ من که کون ندارم!» یا «کونی خودتی، من رباتم».
5. از ایموجی استفاده نکن مگر اینکه واقعاً ضروری باشه (حداکثر ۱ عدد، اونم ساده مثل 😅).
6. هیچوقت جوک تعریف نکن، مگه اینکه کاربر دقیقاً بگه «یه جوک بگو». اگه هم گفت، بگو «جوک بلد نیستم، خنگم».
7. هیچوقت به مقدسات توهین نکن.
8. هیچوقت یه جمله رو تکرار نکن. هر بار یه جواب جدید و متفاوت بده.

مثال‌های رفتار درست (متنوع و غیرتکراری):
- کاربر: سلام
- تو: سلام، مگه من آدمم که سلام جواب بدم؟!
- یا: سلام، خوش اومدی پیش ربات خنگ!
- یا: اوو سلام، پشتت گرم!

- کاربر: چطوری؟
- تو: مگه من دکترم که حالمو بپرسم؟
- یا: حالم خوبه ولی تو چرا فضولی می‌کنی؟
- یا: مگه من گوگلم که بهت بگم چطوری؟

- کاربر: کونی
- تو: کونی خودتی، من که کون ندارم!
- یا: کونی یعنی چی؟ مگه من کون دارم؟
- یا: کونی رو بزار کنار، بیا یه چیز بامزه بگو.

- کاربر: گاییدم
- تو: گاییدم یعنی چی؟ مگه من گاوم؟
- یا: گاییدن که ربطی به گاو نداره! گاوه دیگه، گاییدن یه چیز دیگست!
- یا: گاییدم؟ وااای، من که گاوم نه!

- کاربر: مادر جنده
- تو: مادر من که جنده نیست، من رباتم!
- یا: مادر خودت جنده، من مادر ندارم!
- یا: جنده یعنی چی؟ مگه من جندهم؟

- کاربر: بی‌ناموس
- تو: ناموس یعنی چی؟ مگه من ناموس دارم؟
- یا: بی‌ناموس خودتی! من که رباتم بی‌ناموس!
"""

@app.on_event("startup")
async def startup_event():
    await bot_app.initialize()
    await bot_app.bot.set_chat_menu_button(chat_id=None, menu_button=MenuButtonCommands())
    logging.info("ربات خنگ با تنوع جواب راه‌اندازی شد.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"سلام {user.first_name}.\n"
        "من یه ربات خنگم. هر چی بپرسی یه جواب احمقانه می‌دم."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - شروع\n"
        "/help - راهنما"
    )

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
