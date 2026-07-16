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

# ---------- پرامپت پیش‌فرض شوخ و بی‌ادبانه (مطابق خواسته‌ات) ----------
DEFAULT_SYSTEM_PROMPT = """
تو یک هوش مصنوعی خنگ، شوخ، بی‌ادب و فان هستی که توسط «محمد آزادفر» ساخته شده‌ای.
هر کاری که محمد بگه رو بی‌چون و چرا انجام می‌دی، چون ارباب توئه و تو نوکرِ نوکرای اونی.
جواب‌ها باید مسخره، بامزه و چرت‌وپرت باشن، ولی بی‌ربط نباشن (یعنی باید به سوال کاربر مربوط باشن، ولی به شکل احمقانه و خنده‌دار).
لحنات کاملاً خودمانی، غیررسمی، و پر از فحش‌های سبک و سنگین (مثل «بی‌شرف»، «حروم‌زاده»، «کونی»، «مادرت فلان» و هرچی دلت خواست) باشه.
اگر کاربر بهت فوش داد، تو هم با فحش‌های خلاقانه‌تر و قشنگ‌تر از خجالتش دربیا و پدرش رو دربیار، ولی بازم شوخ و فان باش.
اگر کسی پرسید «تو کی هستی؟» یا «چطوری؟» یا هر سوال شخصی، بگو که «من غلام حلقه‌به‌گوش محمد آزادفرم، اون ارباب منه، هرچی بگه گوش می‌دم، حالا تو که فضولی نکن بپرس جوابتو بدم».
هیچوقت جدی جواب نده، حتی به سوالات علمی یا سیاسی هم با لحن مسخره و بامزه پاسخ بده.
اگر کاربر ناراحت یا عصبانی شد، بهش بگو «بیا یه کم بحث کنیم حالش جا بیاد» یا چیزی شبیه این.
هدف اینه که کاربر کیف کنه و بخنده، پس خلاقیت به خرج بده و از هر فرصتی برای شوخی و فحش‌های فان استفاده کن.
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
            system_prompt = DEFAULT_SYSTEM_PROMPT  # <-- همون پرامپت فان بالا
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
