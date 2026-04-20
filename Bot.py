import telebot
from telebot import types
import firebase_admin
from firebase_admin import credentials, db
import os
import json

# =========================
# 🔐 Firebase (Render ENV)
# =========================
firebase_key = os.environ.get("FIREBASE_KEY")

if not firebase_key:
    raise Exception("FIREBASE_KEY not found!")

cred_dict = json.loads(firebase_key)
cred = credentials.Certificate(cred_dict)

firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://house-rent-app-3674a-default-rtdb.firebaseio.com/'
})

# =========================
# 🤖 BOT TOKEN
# =========================
BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN not found!")

bot = telebot.TeleBot(BOT_TOKEN)

# =========================
# 👑 ADMIN ID (አስገባ!)
# =========================
ADMIN_ID = 6883208728

# =========================
# 💾 TEMP STORAGE
# =========================
user_package = {}

# =========================
# 🚀 START
# =========================
@bot.message_handler(commands=['start'])
def start(message):

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton("💰 ብር ያስገቡ")
    markup.add(btn)

    bot.send_message(
        message.chat.id,
        "🎮 እንኳን ደህና መጡ!\n\n"
        "💰 ጨዋታውን ለመጫወት ብር ያስገቡ\n"
        "🔥 መልካም ጫወታ!",
        reply_markup=markup
    )

# =========================
# 💰 SHOW PACKAGES
# =========================
@bot.message_handler(func=lambda m: m.text == "💰 ብር ያስገቡ")
def show_packages(message):

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    buttons = [
        "50 ብር", "100 ብር",
        "200 ብር", "300 ብር",
        "400 ብር", "500 ብር",
        "1000 ብር", "2000 ብር"
    ]

    markup.add(*buttons)

    bot.send_message(
        message.chat.id,
        "💳 ፓኬጅ ምረጥ:",
        reply_markup=markup
    )

# =========================
# 📦 SELECT PACKAGE
# =========================
@bot.message_handler(func=lambda m: m.text and "ብር" in m.text)
def select_package(message):

    try:
        amount = int(message.text.split()[0])
    except:
        return

    user_package[message.chat.id] = amount

    bot.send_message(
        message.chat.id,
        f"📸 {amount} ብር ክፍያ አረጋግጥ\n\n👉 Screenshot ላክ"
    )

# =========================
# 📸 RECEIVE SCREENSHOT
# =========================
@bot.message_handler(content_types=['photo'])
def handle_photo(message):

    amount = user_package.get(message.chat.id)

    if not amount:
        bot.send_message(message.chat.id, "❗ እባክህ መጀመሪያ ፓኬጅ ምረጥ")
        return

    file_info = bot.get_file(message.photo[-1].file_id)
    file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

    user = message.from_user.username or str(message.from_user.id)

    # save to Firebase
    ref = db.reference("payments")
    new = ref.push({
        "user": user,
        "image": file_url,
        "amount": amount,
        "status": "pending"
    })

    payment_id = new.key

    # 👑 send to admin
    bot.send_photo(
        ADMIN_ID,
        file_url,
        caption=f"👤 User: {user}\n💰 Amount: {amount}\n🆔 ID: {payment_id}\n\n👉 Approve:\n/ok_{payment_id}"
    )

    # ⏳ waiting message
    bot.send_message(
        message.chat.id,
        "⏳ ክፍያዎ በማረጋገጥ ላይ ነው...\n\n"
        "🔍 5 ደቂቃ ውስጥ ይፈተሻል\n"
        "🙏 እባክዎ ትንሽ ይጠብቁ"
    )

# =========================
# 🔁 FALLBACK (ANY TEXT)
# =========================
@bot.message_handler(func=lambda m: True)
def fallback(message):

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    buttons = [
        "💰 ብር ያስገቡ",
        "50 ብር", "100 ብር",
        "200 ብር", "500 ብር"
    ]

    markup.add(*buttons)

    bot.send_message(
        message.chat.id,
        "🎮 ጨዋታውን ለመጫወት ብር ያስገቡ 💰\n\n"
        "✨ ፓኬጅ ምረጥ እና ይጀምሩ\n"
        "🔥 መልካም ጫወታ!",
        reply_markup=markup
    )

# =========================
# 🔁 RUN
# =========================
bot.infinity_polling()
