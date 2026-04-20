import telebot
from telebot import types
import firebase_admin
from firebase_admin import credentials, db
import os
import json

# =========================
# 🔐 Firebase
# =========================
firebase_key = os.environ.get("FIREBASE_KEY")

if not firebase_key:
    raise Exception("FIREBASE_KEY not found")

cred_dict = json.loads(firebase_key)
cred = credentials.Certificate(cred_dict)

firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://house-rent-app-3674a-default-rtdb.firebaseio.com/'
})

# =========================
# 🤖 Bot
# =========================
BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN not found")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

ADMIN_ID = 6883208728

# 👉 memory
user_data = {}

# =========================
# 🎮 MENU
# =========================
def show_menu(chat_id):

    markup = types.InlineKeyboardMarkup(row_width=2)

    markup.add(
        types.InlineKeyboardButton("💰 50 ብር", callback_data="pay_50"),
        types.InlineKeyboardButton("💰 100 ብር", callback_data="pay_100"),
        types.InlineKeyboardButton("💰 200 ብር", callback_data="pay_200"),
        types.InlineKeyboardButton("💰 300 ብር", callback_data="pay_300"),
        types.InlineKeyboardButton("💰 500 ብር", callback_data="pay_500"),
        types.InlineKeyboardButton("💰 1000 ብር", callback_data="pay_1000"),
        types.InlineKeyboardButton("💳 ባላንስ እይ", callback_data="check_balance")
    )

    bot.send_message(
        chat_id,
        "<b>🎮 ለመጫወት ብር ያስገቡ / ፓኬጅ ይግዙ 👇</b>\n\n"
        "<i>🔥 መልካም ጫወታ!</i>",
        reply_markup=markup
    )

# =========================
# 🚀 START
# =========================
@bot.message_handler(commands=['start'])
def start(message):
    show_menu(message.chat.id)

# =========================
# 📦 PACKAGE
# =========================
@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def package(call):

    amount = call.data.split("_")[1]
    user_data[call.from_user.id] = {"amount": amount}

    bot.send_message(
        call.message.chat.id,
        f"<b>✅ {amount} ብር መርጠዋል!</b>\n\n"
        "<b>💳 ክፍያ መረጃ</b>\n"
        "🏦 CBE: 1000641057146\n"
        "📱 0952346729\n\n"
        "<b>📸 screenshot ላኩ</b>"
    )

# =========================
# 💳 BALANCE
# =========================
@bot.callback_query_handler(func=lambda call: call.data == "check_balance")
def balance(call):

    user_id = call.from_user.id
    user_ref = db.reference(f"users/{user_id}")
    data = user_ref.get() or {}

    balance = data.get("balance", 0)

    bot.send_message(
        call.message.chat.id,
        f"<b>💰 የእርስዎ ባላንስ:</b> {balance} ብር"
    )

# =========================
# 📸 PHOTO
# =========================
@bot.message_handler(content_types=['photo', 'document'])
def photo(message):

    try:
        user = user_data.get(message.from_user.id)

        if not user or "amount" not in user:
            bot.send_message(
                message.chat.id,
                "<b>❗ ብር ሳይመርጡ ክፍያ ላኩ!</b>\n📞 0952346729"
            )
            return

        amount = user["amount"]

        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
        else:
            file_id = message.document.file_id

        file_info = bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

        # 👉 save payment
        payment_ref = db.reference("payments").push({
            "user": message.from_user.username,
            "user_id": message.from_user.id,
            "amount": amount,
            "image": file_url,
            "status": "pending"
        })

        payment_id = payment_ref.key

        # 👉 buttons
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{payment_id}"),
            types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{payment_id}")
        )

        # 👉 send to admin
        bot.send_photo(
            ADMIN_ID,
            file_id,
            caption=f"<b>👤 @{message.from_user.username}</b>\n💰 {amount} ብር",
            reply_markup=markup
        )

        bot.send_message(
            message.chat.id,
            "<b>⏳ በማረጋገጥ ላይ ነው...</b>\n\n⌛ 5 ደቂቃ ይጠብቁ"
        )

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ {str(e)}")

# =========================
# ✅ ADMIN ACTION
# =========================
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_"))
def admin_action(call):

    action, payment_id = call.data.split("_")

    ref = db.reference(f"payments/{payment_id}")
    data = ref.get()

    if not data:
        bot.answer_callback_query(call.id, "❌ not found")
        return

    user_id = data["user_id"]
    amount = int(data["amount"])

    if action == "approve":

        ref.update({"status": "approved"})

        user_ref = db.reference(f"users/{user_id}")
        user_data_db = user_ref.get() or {}

        old_balance = user_data_db.get("balance", 0)
        new_balance = old_balance + amount

        user_ref.update({"balance": new_balance})

        bot.send_message(
            user_id,
            f"<b>✅ ተረጋግጧል!</b>\n💰 {amount} ብር ተጨምሯል\n\n🎮 መልካም ጫወታ!"
        )

        bot.answer_callback_query(call.id, "Approved")

    else:

        ref.update({"status": "rejected"})

        bot.send_message(
            user_id,
            "<b>❌ አልተረጋገጠም!</b>\n📞 0952346729"
        )

        bot.answer_callback_query(call.id, "Rejected")

# =========================
# 🔁 TEXT
# =========================
@bot.message_handler(content_types=['text'])
def all_text(message):
    if message.text != "/start":
        show_menu(message.chat.id)

# =========================
# 🚀 RUN
# =========================
bot.infinity_polling()
