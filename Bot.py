import telebot
import firebase_admin
from firebase_admin import credentials, db

# Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://house-rent-app-3674a-default-rtdb.firebaseio.com/'
})

# Bot
bot = telebot.TeleBot("8745422627:AAERWsa1AoBHwkYE2RxXLoT_EolhcdUulfA")

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Screenshot ላክ 📸")

# 📸 Screenshot receive
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"

        username = message.from_user.username or message.from_user.first_name

        ref = db.reference("screenshots")
        ref.push({
            "user": username,
            "image": file_url
        })

        bot.send_message(message.chat.id, "✅ ተቀባ!")

    except Exception as e:
        bot.send_message(message.chat.id, "❌ Error አለ")
        print(e)

bot.infinity_polling()
