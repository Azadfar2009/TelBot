import os
import logging
from datetime import datetime
import pytz  # برای تبدیل ساعت به ایران
from fastapi import FastAPI, Request, Response
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ContextTypes, CallbackQueryHandler, 
    ConversationHandler
)
import uvicorn

# ------- تنظیمات اولیه -------
logging.basicConfig(level=logging.INFO)
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN تنظیم نشده!")

app = FastAPI()
bot_app = Application.builder().token(TOKEN).build()

# مرحله‌های مکالمه (برای دستور feedback)
FEEDBACK_STATE = 1

# دیکشنری برای ذخیره موقت نظرات کاربران (در حافظه سرور)
user_feedback = {}

# دیکشنری برای شمارش تعداد پیام‌های هر کاربر (کاربری)
user_message_count = {}

@app.on_event("startup")
async def init_bot():
    await bot_app.initialize()
    logging.info("ربات با موفقیت مقداردهی اولیه شد.")

# ==========================================
# ---------- توابع ربات (هسته اصلی) ----------
# ==========================================

# 1. دستور start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"سلام {user.first_name} عزیز! 👋\n"
        "من یک ربات حرفه‌ای‌تر شدم!\n\n"
        "🔹 /menu - نمایش منوی اصلی\n"
        "🔹 /stats - تعداد پیام‌های شما\n"
        "🔹 /feedback - ثبت نظر شما\n"
        "🔹 /start - مشاهده همین پیام"
    )

# 2. دستور منو (با دکمه‌های شیشه‌ای)
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🕒 ساعت و تاریخ", callback_data="time"),
            InlineKeyboardButton("📢 درباره ما", callback_data="about"),
        ],
        [
            InlineKeyboardButton("📞 تماس با پشتیبان", callback_data="contact"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "📋 لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=reply_markup
    )

# 3. مدیریت کلیک روی دکمه‌ها (CallbackQuery)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # برای حذف حالت بارگذاری دکمه
    
    data = query.data
    
    if data == "time":
        # نمایش ساعت ایران (حتما کتابخانه pytz را نصب کن، یا از datetime معمولی استفاده کن)
        try:
            tz = pytz.timezone('Asia/Tehran')
            now = datetime.now(tz)
            text = f"🕒 ساعت ایران: {now.strftime('%H:%M:%S')}\n📅 تاریخ: {now.strftime('%Y/%m/%d')}"
        except:
            # اگر pytz نصب نبود، از ساعت جهانی استفاده کن
            now = datetime.now()
            text = f"🕒 ساعت جهانی: {now.strftime('%H:%M:%S')}\n📅 تاریخ: {now.strftime('%Y/%m/%d')}"
        
        await query.edit_message_text(text=text)
        
    elif data == "about":
        await query.edit_message_text(
            "🤖 این ربات با استفاده از FastAPI و Python ساخته شده.\n"
            "هدف آن تمرین توسعه ربات‌های حرفه‌ای با Webhook است.\n"
            "ورژن: 2.0 (پیشرفته)"
        )
    elif data == "contact":
        await query.edit_message_text(
            "📧 برای ارتباط با پشتیبان، می‌توانید به ایمیلی که در بیوگرافی است پیام دهید.\n"
            "یا همینجا از طریق دستور /feedback نظر خود را بنویسید."
        )

# 4. شمارش پیام‌های کاربر
async def count_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # افزایش شمارش
    user_message_count[user_id] = user_message_count.get(user_id, 0) + 1

# 5. دستور آمار (stats)
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    count = user_message_count.get(user_id, 0)
    await update.message.reply_text(
        f"📊 تعداد پیام‌هایی که تا الان برای من فرستاده‌ای: {count} عدد"
    )

# 6. شروع مکالمه (دستور feedback)
async def feedback_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💬 لطفاً نظر یا پیشنهاد خود را درباره ربات بنویسید.\n"
        "(برای لغو عملیات، کلمه 'لغو' را بفرستید.)"
    )
    return FEEDBACK_STATE

# 7. دریافت نظر کاربر در مرحله بعدی مکالمه
async def feedback_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    if user_text == "لغو":
        await update.message.reply_text("❌ عملیات نظرخواهی لغو شد.")
        return ConversationHandler.END
    
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    # ذخیره نظر در دیکشنری (می‌توانی بعداً به دیتابیس وصل کنی)
    user_feedback[user_id] = user_text
    
    await update.message.reply_text(
        f"✅ نظر شما با موفقیت ثبت شد!\n"
        f"متن نظر: {user_text}\n\n"
        "از همراهی شما سپاسگزارم 🙏"
    )
    # تمام کردن مکالمه
    return ConversationHandler.END

# 8. لغو کننده دستی (اگر کاربر در حین مکالمه 'لغو' بزند)
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("عملیات لغو شد.")
    return ConversationHandler.END

# 9. پاسخ به پیام‌های معمولی (با شمارش)
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # شمارش پیام
    await count_messages(update, context)
    
    # پاسخ هوشمندانه به جای اکو ساده
    text = update.message.text
    response = f"📨 پیام شما دریافت شد!\nمتن: {text}\n\n💡 برای مشاهده منو، /menu را بزنید."
    await update.message.reply_text(response)

# ==========================================
# ---------- ثبت همه دستورات و هندلرها ----------
# ==========================================

# دستورات ساده
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("menu", menu))
bot_app.add_handler(CommandHandler("stats", stats))

# هندلر دکمه‌ها (برای /menu)
bot_app.add_handler(CallbackQueryHandler(button_handler))

# هندلر مکالمه (برای /feedback)
feedback_handler = ConversationHandler(
    entry_points=[CommandHandler("feedback", feedback_start)],
    states={
        FEEDBACK_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, feedback_receive)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
bot_app.add_handler(feedback_handler)

# هندلر پیام‌های معمولی (همان اکو هوشمند)
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# ==========================================
# ---------- مسیر Webhook و اجرا ----------
# ==========================================

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
    return {"status": "ربات حرفه‌ای فعال است!"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
