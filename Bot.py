import telebot
from telebot import types
import firebase_admin
from firebase_admin import credentials, db
import os
import json

# 🔐 Firebase
firebase_key = os.environ.get("FIREBASE_KEY")
cred_dict = json.loads(firebase_key)
cred = credentials.Certificate(cred_dict)

firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://house-rent-app-3674a-default-rtdb.firebaseio.com/'
})

# 🤖 Bot
BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

ADMIN_ID = 6883208728

# 👉 user state
user_data = {}

# =========================
# 🎮 MAIN MENU (ANY TEXT)
# =========================
def show_menu(chat_id):

    markup = types.InlineKeyboardMarkup(row_width=2)

    buttons = [
        types.InlineKeyboardButton("50 ብር", callback_data="pay_50"),
        types.InlineKeyboardButton("100 ብር", callback_data="pay_100"),
        types.InlineKeyboardButton("200 ብር", callback_data="pay_200"),
        types.InlineKeyboardButton("300 ብር", callback_data="pay_300"),
        types.InlineKeyboardButton("500 ብር", callback_data="pay_500"),
        types.InlineKeyboardButton("1000 ብር", callback_data="pay_1000"),
    ]

    markup.add(*buttons)

    bot.send_message(
        chat_id,
        "🎮 ለመጫወት ብር ያስገቡ / ፓኬጅ ይግዙ 👇\n\n"
        "✨ ፓኬጅ ይምረጡ\n\n"
        "🔥 መልካም ጫወታ!",
        reply_markup=markup
    )

# =========================
# 🚀 START
# =========================
@bot.message_handler(commands=['start'])
def start(message):
    show_menu(message.chat.id)

# =========================
# 🔁 ANY TEXT
# =========================
@bot.message_handler(func=lambda message: True, content_types=['text'])
def all_text(message):
    show_menu(message.chat.id)

# =========================
# 📦 PACKAGE SELECT
# =========================
@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def package(call):

    amount = call.data.split("_")[1]
    user_data[call.from_user.id] = {"amount": amount}

    bot.send_message(
        call.message.chat.id,
        f"✅ {amount} ብር መርጠዋል!\n\n"
        "💳 ክፍያ መረጃ\n"
        "🏦 CBE: 1000641057146\n"
        "📱 0952346729\n\n"
        "📸 ክፍያ ካደረጉ screenshot ላኩ"
    )

# =========================
# 📸 SCREENSHOT
# =========================
@bot.message_handler(content_types=['photo'])
def photo(message):

    user = user_data.get(message.from_user.id)

    if not user or "amount" not in user:
        bot.send_message(
            message.chat.id,
            "❗ ብር ሳይመርጡ ክፍያ ላኩ!\n\n📞 0952346729"
        )
        return

    amount = user["amount"]

    file_info = bot.get_file(message.photo[-1].file_id)
    file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

    db.reference("payments").push({
        "user": message.from_user.username,
        "amount": amount,
        "image": file_url,
        "status": "pending"
    })

    bot.send_photo(
        ADMIN_ID,
        file_url,
        caption=f"👤 @{message.from_user.username}\n💰 {amount} ብር"
    )

    bot.send_message(
        message.chat.id,
        "⏳ ክፍያዎ በማረጋገጥ ላይ ነው...\n\n⌛ 5 ደቂቃ ይጠብቁ"
    )
