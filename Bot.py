import telebot
from telebot import types
import firebase_admin
from firebase_admin import credentials, db
import os
import json
from flask import Flask
import threading

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
        "💳 CBE: 1000641057146\n"
        "📱 0952346729\n\n"
        "<b>📸 screenshot ላኩ</b>"
    )

# =========================
# 📸 PHOTO
# =========================
@bot.message_handler(content_types=['photo', 'document'])
def photo(message):
    try:
        user = user_data.get(message.from_user.id)

        if not user:
            bot.send_message(message.chat.id, "❗ ብር መርጠው ከዚያ ይላኩ")
            return

        amount = user["amount"]

        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
        else:
            file_id = message.document.file_id

        file_info = bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

        db.reference("payments").push({
            "user": message.from_user.username,
            "user_id": message.from_user.id,
            "amount": amount,
            "image": file_url,
            "status": "pending"
        })

        bot.send_photo(
            ADMIN_ID,
            file_id,
            caption=f"👤 @{message.from_user.username}\n💰 {amount} ብር"
        )

        bot.send_message(
            message.chat.id,
            "<b>⏳ በማረጋገጥ ላይ ነው...</b>\n⌛ 5 ደቂቃ ይጠብቁ"
        )

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ {e}")

# =========================
# 🌐 Flask (IMPORTANT)
# =========================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_bot():
    bot.infinity_polling()

# run bot in thread
threading.Thread(target=run_bot).start()

# run flask
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
