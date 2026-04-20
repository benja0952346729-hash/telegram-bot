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

# 👉 user memory
user_data = {}

# =========================
# 🎮 MENU
# =========================
def show_menu(chat_id):

    markup = types.InlineKeyboardMarkup(row_width=2)

    buttons = [
        types.InlineKeyboardButton("💰 50 ብር", callback_data="pay_50"),
        types.InlineKeyboardButton("💰 100 ብር", callback_data="pay_100"),
        types.InlineKeyboardButton("💰 200 ብር", callback_data="pay_200"),
        types.InlineKeyboardButton("💰 300 ብር", callback_data="pay_300"),
        types.InlineKeyboardButton("💰 500 ብር", callback_data="pay_500"),
        types.InlineKeyboardButton("💰 1000 ብር", callback_data="pay_1000"),
    ]

    markup.add(*buttons)

    bot.send_message(
        chat_id,
        "<b>🎮 ለመጫወት ብር ያስገቡ / ፓኬጅ ይግዙ 👇</b>\n\n"
        "<b>✨ ፓኬጅ ይምረጡ</b>\n\n"
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
# 📦 PACKAGE SELECT
# =========================
@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def package(call):

    amount = call.data.split("_")[1]
    user_data[call.from_user.id] = {"amount": amount}

    bot.send_message(
        call.message.chat.id,
        f"<b>✅ {amount} ብር መርጠዋል!</b>\n\n"
        "<b>💳 ክፍያ መረጃ</b>\n"
        "🏦 <b>CBE:</b> 1000641057146\n"
        "📱 <b>ስልክ:</b> 0952346729\n\n"
        "<b>📸 ክፍያ ካደረጉ screenshot ላኩ</b>"
    )

# =========================
# 📸 PHOTO / DOCUMENT
# =========================
@bot.message_handler(content_types=['photo', 'document'])
def photo(message):
    try:
        user = user_data.get(message.from_user.id)

        if not user or "amount" not in user:
            bot.send_message(
                message.chat.id,
                "<b>❗ ብር ሳይመርጡ ክፍያ ላኩ!</b>\n\n📞 0952346729"
            )
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
            "amount": amount,
            "image": file_url,
            "status": "pending"
        })

        bot.send_photo(
            ADMIN_ID,
            file_url,
            caption=f"<b>👤 @{message.from_user.username}</b>\n💰 {amount} ብር"
        )

        bot.send_message(
            message.chat.id,
            "<b>⏳ ክፍያዎ በማረጋገጥ ላይ ነው...</b>\n\n"
            "<i>⌛ 5 ደቂቃ ይጠብቁ 🙏</i>"
        )

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {str(e)}")

# =========================
# 🔁 TEXT ONLY
# =========================
@bot.message_handler(content_types=['text'])
def all_text(message):
    if message.text != "/start":
        show_menu(message.chat.id)

# =========================
# 🚀 RUN
# =========================
bot.infinity_polling()
