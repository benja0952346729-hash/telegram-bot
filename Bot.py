import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
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

    markup = InlineKeyboardMarkup()

    web_btn = InlineKeyboardButton(
        "🎮 Play Game",
        web_app=WebAppInfo("https://bingo-game-4.onrender.com")
    )

    pay_btn = InlineKeyboardButton("💳 Deposit", callback_data="deposit")
    bal_btn = InlineKeyboardButton("💰 Balance", callback_data="check_balance")

    markup.add(web_btn)
    markup.add(pay_btn, bal_btn)

    bot.send_message(chat_id, "🎮 ጨዋታ ጀምር 👇", reply_markup=markup)

# =========================
# 🚀 START
# =========================
@bot.message_handler(commands=['start'])
def start(message):
    show_menu(message.chat.id)

# =========================
# 💳 DEPOSIT MENU
# =========================
@bot.callback_query_handler(func=lambda call: call.data == "deposit")
def deposit_menu(call):

    markup = types.InlineKeyboardMarkup(row_width=2)

    markup.add(
        types.InlineKeyboardButton("50 ብር", callback_data="pay_50"),
        types.InlineKeyboardButton("100 ብር", callback_data="pay_100"),
        types.InlineKeyboardButton("200 ብር", callback_data="pay_200"),
        types.InlineKeyboardButton("500 ብር", callback_data="pay_500"),
        types.InlineKeyboardButton("1000 ብር", callback_data="pay_1000")
    )

    bot.send_message(call.message.chat.id, "💳 ብር ምረጥ 👇", reply_markup=markup)

# =========================
# 📦 PACKAGE
# =========================
@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def package(call):

    amount = call.data.split("_")[1]
    user_data[call.from_user.id] = {"amount": amount}

    bot.send_message(
        call.message.chat.id,
        f"✅ {amount} ብር መርጠዋል!\n\n"
        "🏦 CBE: 1000641057146\n"
        "📱 0952346729\n\n"
        "📸 screenshot ላኩ"
    )

# =========================
# 💰 BALANCE
# =========================
@bot.callback_query_handler(func=lambda call: call.data == "check_balance")
def balance(call):

    user_id = call.from_user.id
    ref = db.reference(f"users/{user_id}")
    data = ref.get() or {}

    bal = data.get("balance", 0)

    bot.send_message(call.message.chat.id, f"💰 ባላንስ: {bal} ብር")

# =========================
# 📸 PHOTO
# =========================
@bot.message_handler(content_types=['photo', 'document'])
def photo(message):

    try:
        user = user_data.get(message.from_user.id)

        if not user:
            bot.send_message(message.chat.id, "❗ መጀመሪያ ብር ምረጥ")
            return

        amount = int(user["amount"])

        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
        else:
            file_id = message.document.file_id

        file_info = bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

        payment_ref = db.reference("payments").push({
            "user_id": message.from_user.id,
            "amount": amount,
            "image": file_url,
            "status": "pending"
        })

        pid = payment_ref.key

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{pid}"),
            types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{pid}")
        )

        bot.send_photo(
            ADMIN_ID,
            file_id,
            caption=f"💰 {amount} ብር",
            reply_markup=markup
        )

        bot.send_message(message.chat.id, "⏳ በማረጋገጥ ላይ...")

    except Exception as e:
        bot.send_message(message.chat.id, str(e))

# =========================
# ✅ ADMIN
# =========================
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_"))
def admin(call):

    action, pid = call.data.split("_")

    ref = db.reference(f"payments/{pid}")
    data = ref.get()

    if not data:
        return

    user_id = data["user_id"]
    amount = int(data["amount"])

    if action == "approve":

        user_ref = db.reference(f"users/{user_id}")
        user_data_db = user_ref.get() or {}

        old = user_data_db.get("balance", 0)
        new = old + amount

        user_ref.update({"balance": new})

        ref.update({"status": "approved"})

        bot.send_message(user_id, f"✅ {amount} ብር ገብቷል!")

    else:
        ref.update({"status": "rejected"})
        bot.send_message(user_id, "❌ ክፍያ ተቋርጧል")

# =========================
# 🚀 RUN
# =========================
bot.infinity_polling()