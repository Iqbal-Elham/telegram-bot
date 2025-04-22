import logging
from telegram import Update, ChatMember
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import datetime

# توکن ربات خودت را اینجا بگذار
TOKEN = "7960035272:AAFGw7sH89KAw0NCDmOaUK7QqvCsllVSXiQ"

# آیدی عددی خودت را اینجا بگذار
ADMIN_ID = "7859723808"

# فهرست کلمات فحش
BAD_WORDS = ["فحش۱", "فحش۲", "بد", "بی‌ادب", "خر", "احمق", "چیتری"] 

# ذخیره‌ی پیام‌ها و دعوت‌ها
user_messages = {}
user_invites = {}

# تنظیمات لاگ‌برداری (برای بررسی خطا)
logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! من ربات محافظ گروپ هستم. آماده‌ام گروه را پاک نگه دارم!")

def is_bad_word(text):
    for word in BAD_WORDS:
        if word in text:
            return True
    return False

def count_user_messages(user_id):
    now = datetime.datetime.now()
    user_data = user_messages.get(user_id, [])
    # فقط پیام‌های ۲۴ ساعت گذشته
    recent = [msg_time for msg_time in user_data if (now - msg_time).total_seconds() < 86400]
    return len(recent)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type == "private":
        return  # در چت خصوصی کاری نکن

    user = update.message.from_user
    user_id = user.id
    chat_id = update.message.chat_id

    # اگر مدیر باشی، هیچ محدودیت نداری
    if user_id == ADMIN_ID:
        return

    text = update.message.text or ""

    # ۱. جلوگیری از فحش
    if is_bad_word(text.lower()):
        try:
            await context.bot.ban_chat_member(chat_id, user_id)
            await update.message.reply_text("شما به دلیل استفاده از کلمات ناپسند اخراج شدید.")
        except Exception as e:
            logging.error(f"Ban failed: {e}")
        return

    # ۲. جلوگیری از ارسال بیش از ۲ پیام در ۲۴ ساعت
    user_messages.setdefault(user_id, []).append(datetime.datetime.now())
    if count_user_messages(user_id) > 2:
        try:
            await context.bot.delete_message(chat_id, update.message.message_id)
            await context.bot.send_message(chat_id, f"{user.first_name}، شما فقط می‌توانید ۲ پیام در ۲۴ ساعت ارسال کنید.")
        except Exception as e:
            logging.error(f"Delete failed: {e}")
        return

    # ۳. بررسی تعداد دعوت‌ها
    # فقط برای نمونه: اگر کاربر هنوز ۵ نفر دعوت نکرده باشد، نمی‌تواند پیام بفرستد
    invited = user_invites.get(user_id, 0)
    if invited < 5:
        try:
            await context.bot.delete_message(chat_id, update.message.message_id)
            await context.bot.send_message(chat_id, f"{user.first_name}، لطفاً قبل از ارسال پیام ۵ نفر را به گروه دعوت کن.")
        except Exception as e:
            logging.error(f"Delete failed: {e}")
        return

async def invite_checker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "supergroup":
        return

    new_members = update.message.new_chat_members
    inviter = update.message.from_user.id

    if inviter == ADMIN_ID:
        return  # مدیر محدودیت ندارد

    if inviter in user_invites:
        user_invites[inviter] += len(new_members)
    else:
        user_invites[inviter] = len(new_members)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error(msg="Exception caught:", exc_info=context.error)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, invite_checker))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    app.add_error_handler(error_handler)

    print("ربات فعال شد...")
    app.run_polling()
