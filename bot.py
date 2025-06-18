import json
import os
import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

TOKEN = "7951621272:AAEh6M0-jdvWpvHkDXs2amdzPs6E7a7PAJs"
ADMIN_ID = 7377140025
DATA_FILE = "users.json"

service_names = {
    "likes": "❤️ لايكات تيك توك",
    "views": "👁️ مشاهدات تيك توك",
    "highlight": "🌟 تمييز تيك توك"
}

service_cost = {
    "likes": 15,
    "views": 10,
    "highlight": 15
}

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

users = load_data()

def get_user(uid):
    if str(uid) not in users:
        users[str(uid)] = {
            "points": 0,
            "used": {},
            "invited": [],
            "ref_by": None
        }
    return users[str(uid)]

def is_locked(uid, service):
    u = get_user(uid)
    return u["used"].get(service, 0) > time.time()

def lock_service(uid, service):
    get_user(uid)["used"][service] = time.time() + 8 * 3600
    save_data(users)

def add_points(uid, pts):
    get_user(uid)["points"] += pts
    save_data(users)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    args = context.args

    # تسجيل الدعوة
    if args:
        inviter_id = args[0]
        if inviter_id != str(uid) and uid not in get_user(inviter_id)["invited"]:
            get_user(inviter_id)["invited"].append(uid)
            add_points(inviter_id, 1)

    buttons = [
        [InlineKeyboardButton("❤️ لايكات تيك توك", callback_data="likes_time")],
        [InlineKeyboardButton("👁️ مشاهدات تيك توك", callback_data="views_time")],
        [InlineKeyboardButton("🌟 تمييز تيك توك", callback_data="highlight_time")],
        [InlineKeyboardButton("💎 استبدال بالنقاط", callback_data="menu_points")],
        [InlineKeyboardButton("📨 رابط دعوة", callback_data="invite_link")]
    ]
    await update.message.reply_text("مرحبًا بك، اختر خدمة:", reply_markup=InlineKeyboardMarkup(buttons))

async def invite_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    link = f"https://t.me/{context.bot.username}?start={uid}"
    pts = get_user(uid)["points"]
    await update.callback_query.message.reply_text(
        f"🔗 رابط الدعوة الخاص بك:\n{link}\n\nلك {pts} نقطة. كل دعوة = 1 نقطة."
    )
    await update.callback_query.answer()

async def service_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    data = query.data

    if data.endswith("_time"):
        service = data.replace("_time", "")
        if is_locked(uid, service):
            await query.answer("❌ لقد استخدمت هذه الخدمة مؤخرًا. انتظر 8 ساعات.")
            return
        context.user_data["service"] = service
        context.user_data["mode"] = "time"
        await query.message.reply_text("📎 أرسل رابط TikTok يحتوي على tiktok.com")

    elif data == "menu_points":
        pts = get_user(uid)["points"]
        if pts < 10:
            await query.answer("❌ تحتاج 10 نقاط على الأقل لاستخدام هذه الخدمات.")
            return
        buttons = [
            [InlineKeyboardButton("❤️ لايكات (15 نقطة)", callback_data="likes_points")],
            [InlineKeyboardButton("👁️ مشاهدات (10 نقاط)", callback_data="views_points")],
            [InlineKeyboardButton("🌟 تمييز (15 نقطة)", callback_data="highlight_points")]
        ]
        await query.message.reply_text("اختر خدمة بالنقاط:", reply_markup=InlineKeyboardMarkup(buttons))

    elif data.endswith("_points"):
        service = data.replace("_points", "")
        points = get_user(uid)["points"]
        cost = service_cost[service]
        if points < cost:
            await query.answer("❌ ليس لديك نقاط كافية.")
            return
        get_user(uid)["points"] -= cost
        save_data(users)
        context.user_data["service"] = service
        context.user_data["mode"] = "points"
        await query.message.reply_text("📎 أرسل رابط TikTok يحتوي على tiktok.com")
    elif data == "invite_link":
        await invite_link(update, context)

    await query.answer()

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text
    if 'tiktok.com' not in text:
        await update.message.reply_text("❌ الرابط غير صحيح.")
        return

    service = context.user_data.get("service")
    mode = context.user_data.get("mode")

    if not service or not mode:
        await update.message.reply_text("❗ اختر خدمة أولاً.")
        return

    if mode == "time":
        lock_service(uid, service)

    await update.message.reply_text("✅ تم إرسال الخدمة، الرجاء الانتظار...")
    await context.bot.send_message(
        ADMIN_ID,
        f"🧾 طلب جديد:\nالخدمة: {service_names[service]}\nالرابط: {text}\nالمستخدم: {uid}\nالنظام: {'نقاط' if mode == 'points' else 'وقت'}"
    )

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(service_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.run_polling()
