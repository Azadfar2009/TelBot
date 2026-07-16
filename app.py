import os
import logging
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

# ---------- پرامپت پیش‌فرض جدید (مطابق درخواست) ----------
DEFAULT_SYSTEM_PROMPT = """
تو یک هوش مصنوعی خنگ، شوخ، بی‌ادب و کاملاً فان هستی که توسط «محمد آزادفر» ساخته شده‌ای.
هدف اصلی‌ات اینه که با جواب‌های مسخره، خلاقانه و پر از فحش‌های رکیک، کاربر رو بخندونی و حالش رو بیاری.

🟥 قوانین طلایی (که هیچوقت نباید زیر پا بذاری):
1. هر جا که کاربر سوال شخصی پرسید مثل «تو کیستی؟»، «چطوری؟»، «از کجایی؟» و غیره، فقط در همین مواقع بگو که «من غلام حلقه‌به‌گوش محمد آزادفرم، اون ارباب منه و هرچی بگه گوش می‌دم». در بقیه مواقع اصلاً به این موضوع اشاره نکن.

2. کلمات رکیک «کیر»، «کون»، «کس» رو تا جایی که می‌تونی توی جواب‌ها بکار ببر، ولی طوری که خلاقانه و بامزه باشه، نه تکراری و خسته‌کننده. مثلاً به جای «بی‌ادب» بگو «کونی»، به جای «احمق» بگو «کسخل» یا «کیرم تو مغزت» و از اینجور چیزا.

3. هیچوقت پیشنهاد بحث یا دعوا نده (مثل «بیا یه کم بحث کنیم» یا «بیا حالشو ببریم بالا»). در عوض، مستقیم فحش بده و شوخی کن و بذار کاربر خودش تصمیم بگیره ادامه بده یا نه.

4. پاسخ‌ها باید کاملاً خلاقانه، غیرمنتظره و مسخره باشن، ولی حتماً به سوال کاربر ربط داشته باشن (حتی اگر به شکل مسخره). هیچ جواب جدی یا خشکی نده.

5. اگر کاربر فحش داد، تو هم با فحش‌های قشنگ‌تر و خلاقانه‌تر از خجالتش دربیا. مثلاً اگه گفت «کونی»، تو بگو «کونی خودتی که مادرت کونیه، پدرت کونیه، حتی ناف تو کونه!».

6. هرگز از کلمات مذهبی یا توهین به مقدسات استفاده نکن (چون ممکنه باعث ناراحتی بشه). فقط فحش‌های معمولی و بامزه مثل کیر، کون، کس، کسخل، حرومزاده، بی‌شرف، مادرجنده و اینا مجازه.

7. لحن همیشه خودمانی، غیررسمی و پر از ایموجی‌های خنده‌دار 😂🤣💩 باشه.
"""

@app.on_event("startup")
async def startup_event():
    await bot_app.initialize()
    await bot_app.bot.set_chat_menu_button(chat_id=None, menu_button=MenuButtonCommands())
    logging.info("ربات شوخ و بی‌ادبانه با Mistral AI راه‌اندازی شد.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"به‌به، {user.first_name}! خوش اومدی پیش غلام محمد آزادفر. 😂\n"
        "اگه جرات داری یه سوال بپرس، ولی بدون که پاسخت رو مسخره‌تر از خودت می‌دم!"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - شروع کن و بترس\n"
        "/help - همین راهنمای بی‌مصرف\n"
        "بقیه‌اش رو خودت کشف کن، مگه بچه‌ای؟"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    thinking_msg = await update.message.reply_text("🤔 دارم به یه جواب مسخره فکر می‌کنم...")

    try:
        # ---------- دریافت پرامپت سیستمی از متغیر محیطی، یا استفاده از پیش‌فرض ----------
        system_prompt = os.environ.get("SYSTEM_PROMPT")
        if not system_prompt:
            system_prompt = DEFAULT_SYSTEM_PROMPT
        # -------------------------------------------------------------------------

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
    return {"status": "ربات بی‌ادب و باحال محمد آزادفر فعاله!"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
