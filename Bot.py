import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

import firebase_admin
from firebase_admin import credentials, db

import os
import json
import threading
from flask import Flask

# =========================
# 🔥 FLASK KEEP ALIVE
# =========================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask, daemon=True).start()

# =========================
# 🔐 FIREBASE INIT
# =========================
firebase_key = os.environ.get("FIREBASE_KEY")
if not firebase_key:
    raise Exception("❌ FIREBASE_KEY not found")

cred_dict = json.loads(firebase_key)
cred = credentials.Certificate(cred_dict)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://house-rent-app-3674a-default-rtdb.firebaseio.com/'
    })

# =========================
# 🤖 BOT INIT
# =========================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise Exception("❌ BOT_TOKEN not found")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

ADMIN_ID = 6883208728

# ⚠ FIX: use Firebase instead of RAM (important fix)
user_cache = {}

# =========================
# 🎮 MENU
# =========================
def show_menu(chat_id):
    markup = InlineKeyboardMarkup()

    web_btn = InlineKeyboardButton(
        "🎮 Play Game",
        web_app=WebAppInfo(
            url=f"https://bingo-game-4.onrender.com/?uid={chat_id}"
        )
    )

    markup.add(web_btn)
    markup.add(
        InlineKeyboardButton("💳 Deposit", callback_data="deposit"),
        InlineKeyboardButton("💰 Balance", callback_data="balance")
    )

    bot.send_message(chat_id, "🎮 ጨዋታ ጀምር 👇", reply_markup=markup)

# =========================
# 🚀 START
# =========================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id

    # create user if not exists
    ref = db.reference(f"users/{user_id}")
    if not ref.get():
        ref.set({"balance": 0})

    show_menu(message.chat.id)

# =========================
# 💳 DEPOSIT MENU
# =========================
@bot.callback_query_handler(func=lambda call: call.data == "deposit")
def deposit_menu(call):
    markup = types.InlineKeyboardMarkup(row_width=2)

    amounts = [50, 100, 200, 500, 1000]

    buttons = [
        types.InlineKeyboardButton(f"{a} ብር", callback_data=f"pay_{a}")
        for a in amounts
    ]

    markup.add(*buttons)

    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "💳 ብር ምረጥ 👇", reply_markup=markup)

# =========================
# 📦 PACKAGE SELECT
# =========================
@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def package(call):

    amount = int(call.data.split("_")[1])
    user_cache[call.from_user.id] = amount  # TEMP STORAGE

    bot.answer_callback_query(call.id)

    bot.send_message(
        call.message.chat.id,
        f"""✅ {amount} ብር መርጠዋል!

🏦 CBE: 1000641057146
📱 0952346729

📸 screenshot ላኩ"""
    )

# =========================
# 💰 BALANCE
# =========================
@bot.callback_query_handler(func=lambda call: call.data == "balance")
def balance(call):

    bot.answer_callback_query(call.id)

    user_id = call.from_user.id
    ref = db.reference(f"users/{user_id}")
    data = ref.get() or {}

    bot.send_message(
        call.message.chat.id,
        f"💰 ባላንስ: <b>{data.get('balance', 0)}</b> ብር"
    )

# =========================
# 📸 PAYMENT PROOF
# =========================
@bot.message_handler(content_types=['photo', 'document'])
def handle_payment(message):

    user_id = message.from_user.id

    # FIX: check safe
    if user_id not in user_cache:
        bot.send_message(message.chat.id, "❗ መጀመሪያ ብር ምረጥ")
        return

    amount = user_cache[user_id]

    file_id = None
    if message.content_type == 'photo':
        file_id = message.photo[-1].file_id
    else:
        file_id = message.document.file_id

    payment_ref = db.reference("payments").push({
        "user_id": user_id,
        "amount": amount,
        "file_id": file_id,
        "status": "pending"
    })

    pid = payment_ref.key

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ Approve", callback_data=f"approve_{pid}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"reject_{pid}")
    )

    bot.send_photo(
        ADMIN_ID,
        file_id,
        caption=f"💰 {amount} ብር\nUser: {user_id}",
        reply_markup=markup
    )

    bot.send_message(message.chat.id, "⏳ በማረጋገጥ ላይ...")

# =========================
# ✅ ADMIN ACTION
# =========================
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_"))
def admin_action(call):

    bot.answer_callback_query(call.id)

    action, pid = call.data.split("_")

    ref = db.reference(f"payments/{pid}")
    data = ref.get()

    if not data:
        return

    user_id = data["user_id"]
    amount = int(data["amount"])

    user_ref = db.reference(f"users/{user_id}")
    user_data = user_ref.get() or {}

    if action == "approve":

        new_balance = user_data.get("balance", 0) + amount

        user_ref.update({"balance": new_balance})
        ref.update({"status": "approved"})

        bot.send_message(user_id, f"✅ {amount} ብር ገብቷል!")

    else:
        ref.update({"status": "rejected"})
        bot.send_message(user_id, "❌ ክፍያ ተቋርጧል")

# =========================
# 🚀 RUN
# =========================
print("🤖 Bot started...")
bot.infinity_polling(skip_pending=True)