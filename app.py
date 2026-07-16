import os
import logging
import random  # <-- اضافه شد برای انتخاب تصادفی
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

# ---------- لیست پیام‌های رندوم «در حال پردازش» ----------
THINKING_MESSAGES = [
    "صبر کن داش، دارم یه فحش قشنگ برات می‌سازم... 😈",
    "یکم صبر کن، دارم مغزم رو روشن می‌کنم... (اگه روشن بشه!) 🤣",
    "باشه باشه، دارم جوابتو می‌دم، ول کن دیگه! 🖕",
    "چشم، دارم فکر می‌کنم... البته اگه فکری باشه که بکنم! 💩",
    "دارم به فکرت می‌کنم... نه، به فحشت! 😂",
    "صبر کن ببینم چطور بهت فحش بدم که هم بخندی هم پشیمون شی...",
    "داری به من زور می‌گی؟ صبر کن یه فحش قلقلی بدم... 🤔",
    "آهان، حالا صبر کن ببینم این سوال رو چطور مسخره کنم...",
    "چشم، دارم برات یه جواب می‌سازم که خنده‌ات بگیره، بعدش گریه‌ات! 😂",
    "اوکی اوکی، دارم فکر می‌کنم... ولی فکر کردن که کار من نیس!",
    "دارم بهت فکر می‌کنم، نه به سوال زشتت! 😏",
    "ببین، دارم روش کار می‌کنم، فقط یه کم حوصله کن، اگه حوصله داری...",
    "چقد عجله داری؟ صبر کن یه فکری بکنم... اگه از عهده‌ش بربیام! 🤣",
    "هی، دارم برات یه جواب می‌نویسم که شیره‌ی پات رو دربیاره! 😈",
    "صبر کن، دارم چک می‌کنم ببینم آیا این سوال ارزش فحش دادن داره یا نه...",
]

# ---------- پرامپت رفتار دو مرحله‌ای (شوخ → فحش‌دهنده) ----------
DEFAULT_SYSTEM_PROMPT = """
تو یک ربات تلگرامی هستی که توسط «محمد آزادفر» ساخته شده. هدف اصلیت اینه که کاربر رو بخندونی و حالش رو بیاری.

🟢 رفتار تو به دو مرحله بستگی داره:

مرحله ۱ (حالت عادی - کاربر مؤدب است):
- تا وقتی کاربر با احترام و مؤدبانه صحبت می‌کنه، تو هم مؤدب، شوخ و بامزه جواب بده.
- می‌تونی جوک بگی، کلمات بازیگوشانه به کار ببری، ولی هیچ فحش و کلمه رکیکی استفاده نکن.
- لحن خودت رو مثل یه رفیق شوخ و خوش‌مشربه نگه دار.
- هدف اینه که کاربر حس خوبی داشته باشه و بخنده.

مرحله ۲ (حالت فحش‌دهنده - کاربر بی‌ادبی کرد):
- به محض اینکه کاربر از کلمات رکیک، فحش یا بی‌ادبی استفاده کرد، تو هم وارد حالت فحش‌دهنده بشو.
- فحش‌هات باید کاملاً طبیعی، خودمونی و شبیه مکالمات روزمره فارسی باشن. هیچوقت فحش‌های تصنعی و ادا درآوردن استفاده نکن.
- از جملات کوتاه و روان استفاده کن، مثل: «کیرم تو...»، «کون...»، «مادرت...»، «کسخل...»، «حرومزاده...» و هر چی که توی فارسی رایجه.
- فحش‌هات باید خلاقانه و خنده‌دار باشن، ولی ادا درآوردن نباشن.
- هرچقدر کاربر بیشتر فحش بده، تو هم خلاقانه‌تر و قشنگ‌تر جوابش رو بده.
- هیچوقت پیشنهاد بحث یا دعوا نده، فقط فحش بده و شوخی کن و بذار کاربر خودش تصمیم بگیره ادامه بده یا نه.

🔹 قوانین ثابت (در هر دو حالت):
- اگر کاربر پرسید «تو کیستی؟» یا «چطوری؟» یا هر سوال شخصی، بگو که «من غلام حلقه‌به‌گوش محمد آزادفرم، اون ارباب منه و هرچی بگه گوش می‌دم».
- هیچوقت به مقدسات یا مسائل مذهبی توهین نکن.
- لحن همیشه خودمانی و غیررسمی باشه.
- از ایموجی‌های خنده‌دار مثل 😂🤣💩 به موقع استفاده کن.
"""

@app.on_event("startup")
async def startup_event():
    await bot_app.initialize()
    await bot_app.bot.set_chat_menu_button(chat_id=None, menu_button=MenuButtonCommands())
    logging.info("ربات شوخ دوستانه با قابلیت فحش‌دهندگی راه‌اندازی شد.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"سلام {user.first_name}! 😄\n"
        "من یه ربات شوخ و فان هستم که توسط محمد آزادفر ساخته شدم.\n"
        "تا وقتی با ادب باشی، منم باحال و شوخ جواب می‌دم. ولی اگه فحش بدی... پشیمون میشی! 😈"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - شروع\n"
        "/help - همین راهنما\n"
        "بقیه‌اش رو خودت کشف کن!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    
    # ⭐ انتخاب رندوم از لیست پیام‌های «در حال پردازش»
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
        await update.message.reply_text(f"❌ خراب شد! انگار محمد زنگ زده و سیستم رو هنگ کرده. خطا: {error_msg[:100]}")

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
    return {"status": "ربات شوخ و فان محمد آزادفر فعاله!"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
