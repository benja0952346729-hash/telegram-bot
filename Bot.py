import telebot
import firebase_admin
from firebase_admin import credentials, db
import os
import json

# 🔐 Firebase key from ENV (Render)
firebase_key = os.environ.get("FIREBASE_KEY")

if not firebase_key:
    raise Exception("FIREBASE_KEY not found!")

cred_dict = json.loads(firebase_key)

cred = credentials.Certificate(cred_dict)

firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://house-rent-app-3674a-default-rtdb.firebaseio.com/'
})

# 🤖 Telegram Bot Token (ENV)
BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN not found!")

bot = telebot.TeleBot(BOT_TOKEN)

# 🚀 Start command
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "📸 Screenshot ላክ!")

# 📸 Receive Photo
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

        # save to Firebase
        ref = db.reference("screenshots")
        ref.push({
            "user": message.from_user.username,
            "image": file_url
        })

        bot.send_message(message.chat.id, "✅ ተቀባ!")

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {str(e)}")

# 🔁 Run bot
bot.infinity_polling()
