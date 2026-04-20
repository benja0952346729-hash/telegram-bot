import telebot
from telebot import types
import firebase_admin
from firebase_admin import credentials, db
import os
import json
import time

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

# 👉 Main Menu
def main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("💰 ብር ያስገቡ")
    markup.add(btn1)

    bot.send_message(
        chat_id,
        "🎮 ጫወታ ለመጫወት ብር ያስገቡ\n\n👇 ከታች ይምረጡ",
        reply_markup=markup
    )

# 🚀 Start
@bot.message_handler(commands=['start'])
def start(message):
    main_menu(message.chat.id)

# 💰 Deposit Button
@bot.message_handler(func=lambda m: m.text == "💰 ብር ያስገቡ")
def deposit(message):
    markup = types.InlineKeyboardMarkup()

    prices = [50,100,200,300,400,500,1000,2000]

    for p in prices:
        markup.add(types.InlineKeyboardButton(f"{p} ብር", callback_data=f"pay_{p}"))

    bot.send_message(
        message.chat.id,
        "💳 ፓኬጅ ይምረጡ:",
        reply_markup=markup
    )

# 📦 Package Select
@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def package_selected(call):
    amount = call.data.split("_")[1]

    # save user choice
    ref = db.reference("users").child(str(call.from_user.id))
    ref.update({"amount": amount})

    text = f"""
💳 ክፍያ መረጃ

🏦 CBE: 1000641057146
📱 0952346729

📸 ክፍያ ከፈጸሙ በኋላ screenshot ላኩ
"""

    bot.send_message(call.message.chat.id, text)

# 📸 Screenshot receive
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        user_id = str(message.from_user.id)

        # get selected amount
        ref = db.reference("users").child(user_id)
        data = ref.get()

        if not data or "amount" not in data:
            bot.send_message(message.chat.id, "❗ እባክዎ መጀመሪያ ፓኬጅ ይምረጡ")
            return

        amount = data["amount"]

        # get photo link
        file_info = bot.get_file(message.photo[-1].file_id)
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

        # save to firebase
        db.reference("payments").push({
            "user_id": user_id,
            "username": message.from_user.username,
            "amount": amount,
            "image": file_url,
            "status": "pending"
        })

        # ✅ user message
        bot.send_message(
            message.chat.id,
            "⏳ ክፍያዎ በማረጋገጥ ላይ ነው...\n\n⌛ 5 ደቂቃ ይጠብቁ"
        )

        # 📩 send to admin
        bot.send_photo(
            ADMIN_ID,
            file_url,
            caption=f"""
📥 አዲስ ክፍያ

👤 @{message.from_user.username}
💰 {amount} ብር
"""
        )

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {str(e)}")

# 🔁 ANY TEXT → menu
@bot.message_handler(func=lambda message: True)
def all_text(message):
    main_menu(message.chat.id)

# 🚀 RUN
bot.infinity_polling()
