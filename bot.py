import json
import os
import time
from telegram import *
from telegram.ext import *

TOKEN = "7951621272:AAEh6M0-jdvWpvHkDXs2amdzPs6E7a7PAJs"
ADMIN_ID = 7377140025
DATA_FILE = "users.json"

# تحميل / إنشاء البيانات
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

with open(DATA_FILE, "r") as f:
    users = json.load(f)

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(users, f)

def get_user(uid):
    uid = str(uid)
    if uid not in users:
        users[uid] = {
            "points": 0,
            "invited": [],
            "used": {},
            "ref": None
        }
    return users[uid]

def is_limited(uid, service):
    now = time.time()
    return get_user(uid)["used"].get(service, 0) > now

def set_limit(uid, service, hours=8):
    get_user(uid)["used"][service] = time.time() + hours * 3600
    save_data()

def add_points(uid, count):
    get_user(uid)["points"] += count
    save_data()

def deduct_points(uid, count):
    get_user(uid)["points"] -= count
    save_data()

def start(update, context):
    user = update.message.from_user
    uid = str(user.id)
    args = context.args

    if args:
        ref = args[0]
        if ref != uid:
            u = get_user(uid)
            if not u["ref"]:
                u["ref"] = ref
                if uid not in get_user(ref)["invited"]:
                    get_user(ref)["invited"].append(uid)
                    add_points(ref, 1)

    get_user(uid)  # تأكد من إنشاء المستخدم
    save_data()

    keyboard = [
        [InlineKeyboardButton("❤️ لايكات تيك توك", callback_data="likes")],
        [InlineKeyboardButton("👁️ مشاهدات تيك توك", callback_data="views")],
        [InlineKeyboardButton("🌟 تمييز فيديو", callback_data="highlight")],
        [InlineKeyboardButton("💎 خدمات بالنقاط", callback_data="points")],
        [InlineKeyboardButton("📨 رابط الدعوة", callback_data="invite")],
    ]
    update.message.reply_text("اختر خدمة:", reply_markup=InlineKeyboardMarkup(keyboard))

def button(update, context):
    query = update.callback_query
    uid = query.from_user.id
    data = query.data
    user = get_user(uid)

    if data in ["likes", "views", "highlight"]:
        if is_limited(uid, data):
            query.answer("⏱️ استخدمت الخدمة مؤخرًا. انتظر 8 ساعات.")
            return
        context.user_data["mode"] = "free"
        context.user_data["service"] = data
        query.message.reply_text("📎 أرسل رابط فيديو تيك توك يحتوي على tiktok.com")
    elif data == "points":
        pts = user["points"]
        if pts < 10:
            query.answer("❌ تحتاج 10 نقاط على الأقل.")
            return
        keyboard = [
            [InlineKeyboardButton("❤️ لايكات (15 نقطة)", callback_data="likes_p")],
            [InlineKeyboardButton("👁️ مشاهدات (10 نقاط)", callback_data="views_p")],
            [InlineKeyboardButton("🌟 تمييز (15 نقطة)", callback_data="highlight_p")],
        ]
        query.message.reply_text("اختر خدمة بنظام النقاط:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == "invite":
        link = f"https://t.me/{context.bot.username}?start={uid}"
        query.message.reply_text(f"🔗 رابط الدعوة الخاص بك:\n{link}\nكل دعوة = 1 نقطة")
    elif data.endswith("_p"):
        service = data.replace("_p", "")
        cost = {"likes": 15, "views": 10, "highlight": 15}[service]
        if user["points"] < cost:
            query.answer("❌ ليس لديك نقاط كافية.")
            return
        deduct_points(uid, cost)
        context.user_data["mode"] = "points"
        context.user_data["service"] = service
        query.message.reply_text("📎 أرسل رابط فيديو تيك توك يحتوي على tiktok.com")

    query.answer()

def handle_link(update, context):
    uid = update.message.from_user.id
    text = update.message.text
    if "tiktok.com" not in text:
        update.message.reply_text("❌ الرابط غير صالح.")
        return

    service = context.user_data.get("service")
    mode = context.user_data.get("mode")

    if not service or not mode:
        update.message.reply_text("❗ اختر الخدمة أولاً.")
        return

    if mode == "free":
        set_limit(uid, service)

    update.message.reply_text("✅ تم إرسال الخدمة بنجاح، الرجاء الانتظار...")

    context.bot.send_message(
        ADMIN_ID,
        f"📩 طلب جديد:\nالخدمة: {service}\nالرابط: {text}\nالمستخدم: {uid}\nالنظام: {mode}"
    )

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_link))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
