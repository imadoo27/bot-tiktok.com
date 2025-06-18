from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import time

TOKEN = "7951621272:AAEh6M0-jdvWpvHkDXs2amdzPs6E7a7PAJs"
ADMIN_ID = 7377140025

# قفل الخدمة لكل مستخدم
user_service_locks = {}  # {user_id: {service_name: expire_time}}

# أسماء الخدمات
service_names = {
    'likes': '❤️ لايكات تيك توك',
    'views': '👁️ مشاهدات تيك توك',
    'highlight': '🌟 تمييز تيك توك'
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("❤️ لايكات تيك توك", callback_data='likes')],
        [InlineKeyboardButton("👁️ مشاهدات تيك توك", callback_data='views')],
        [InlineKeyboardButton("🌟 تمييز فيديو", callback_data='highlight')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("اختر الخدمة:", reply_markup=reply_markup)

def is_locked(user_id, service):
    if user_id not in user_service_locks:
        return False
    return user_service_locks[user_id].get(service, 0) > time.time()

def lock_user_service(user_id, service):
    if user_id not in user_service_locks:
        user_service_locks[user_id] = {}
    user_service_locks[user_id][service] = time.time() + 8 * 3600  # 8 ساعات

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    service = query.data

    if is_locked(user_id, service):
        await query.answer("❌ لقد استخدمت هذه الخدمة مؤخرًا. يرجى الانتظار 8 ساعات.")
        return

    context.user_data['service'] = service
    await query.message.reply_text("📎 أرسل رابط فيديو يحتوي على tiktok.com")
    await query.answer()

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    if 'tiktok.com' not in text:
        await update.message.reply_text("❌ الرابط غير صحيح، يجب أن يحتوي على tiktok.com")
        return

    if 'service' not in context.user_data:
        await update.message.reply_text("❗ يرجى اختيار خدمة أولاً.")
        return

    service = context.user_data['service']

    if is_locked(user_id, service):
        await update.message.reply_text("❌ لقد استخدمت هذه الخدمة مؤخرًا. يرجى الانتظار 8 ساعات.")
        return

    await update.message.reply_text("✅ تم إرسال الخدمة، الرجاء الانتظار...")

    # إرسال للادمن
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🧾 طلب جديد:\nالخدمة: {service_names[service]}\nالرابط: {text}\nالمستخدم: {user_id}"
    )

    lock_user_service(user_id, service)

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

    app.run_polling()
