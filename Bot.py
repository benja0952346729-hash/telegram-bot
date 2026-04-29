import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

import firebase_admin
from firebase_admin import credentials, db

import os
import json
from flask import Flask
import threading

# =========================
# FLASK KEEP ALIVE
# =========================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run).start()

# =========================
# FIREBASE INIT
# =========================
cred = credentials.Certificate(json.loads(os.environ["FIREBASE_KEY"]))

firebase_admin.initialize_app(cred, {
    "databaseURL": "https://house-rent-app-3674a-default-rtdb.firebaseio.com/"
})

# =========================
# BOT INIT
# =========================
bot = telebot.TeleBot(os.environ["BOT_TOKEN"], parse_mode="HTML")

ADMIN_ID = 6883208728

# =========================
# MENU
# =========================
def menu(chat_id):
    markup = InlineKeyboardMarkup()

    markup.add(
        InlineKeyboardButton(
            "🎮 Play Game",
            web_app=WebAppInfo(f"https://bingo-game-4.onrender.com/?uid={chat_id}")
        )
    )

    markup.add(
        InlineKeyboardButton("💳 Deposit", callback_data="deposit"),
        InlineKeyboardButton("💰 Balance", callback_data="balance")
    )

    bot.send_message(chat_id, "🎮 Menu 👇", reply_markup=markup)

# =========================
# START
# =========================
@bot.message_handler(commands=['start'])
def start(m):
    menu(m.chat.id)

# =========================
# DEPOSIT MENU
# =========================
def deposit_menu(call):
    m = InlineKeyboardMarkup(row_width=2)

    for a in [50,100,200,500,1000]:
        m.add(InlineKeyboardButton(f"{a} ብር", callback_data=f"pay_{a}"))

    bot.send_message(call.message.chat.id, "💳 Select amount:", reply_markup=m)

# =========================
# PACKAGE SELECT
# =========================
def package(call):
    user_id = str(call.from_user.id)
    amount = int(call.data.split("_")[1])

    db.reference(f"temp/{user_id}").set({"amount": amount})

    bot.send_message(
        call.message.chat.id,
        f"✅ {amount} ብር selected\n\n"
        "🏦 CBE: 1000641057146\n"
        "📸 send screenshot"
    )

# =========================
# BALANCE
# =========================
def balance(call):
    user_id = str(call.from_user.id)

    data = db.reference(f"users/{user_id}").get() or {}
    bal = data.get("balance", 0)

    bot.send_message(call.message.chat.id, f"💰 Balance: {bal} ብር")

# =========================
# PAYMENT PROOF
# =========================
@bot.message_handler(content_types=['photo','document'])
def proof(m):
    user_id = str(m.from_user.id)

    temp = db.reference(f"temp/{user_id}").get()

    if not temp:
        bot.send_message(m.chat.id, "❗ መጀመሪያ deposit ምረጥ")
        return

    amount = temp["amount"]

    file_id = m.photo[-1].file_id if m.content_type == "photo" else m.document.file_id

    pid = db.reference("payments").push({
        "user_id": user_id,
        "amount": amount,
        "file_id": file_id,
        "status": "pending"
    }).key

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("✅ Approve", callback_data=f"ap_{pid}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"re_{pid}")
    )

    bot.send_photo(
        ADMIN_ID,
        file_id,
        caption=f"💰 {amount} ብር\nUser: {user_id}",
        reply_markup=kb
    )

    bot.send_message(m.chat.id, "⏳ waiting approval...")

# =========================
# ADMIN ACTION
# =========================
def admin(call):
    action, pid = call.data.split("_")

    ref = db.reference(f"payments/{pid}")
    data = ref.get()

    if not data:
        return

    user_id = data["user_id"]
    amount = int(data["amount"])

    if action == "ap":
        uref = db.reference(f"users/{user_id}")
        old = uref.get() or {}

        new_bal = old.get("balance", 0) + amount
        uref.update({"balance": new_bal})

        ref.update({"status": "approved"})
        bot.send_message(user_id, f"✅ {amount} ብር added!")

    else:
        ref.update({"status": "rejected"})
        bot.send_message(user_id, "❌ rejected")

# =========================
# CALLBACK ROUTER (FIXED)
# =========================
@bot.callback_query_handler(func=lambda c: True)
def handle(c):
    bot.answer_callback_query(c.id)

    if c.data == "deposit":
        deposit_menu(c)

    elif c.data == "balance":
        balance(c)

    elif c.data.startswith("pay_"):
        package(c)

    elif c.data.startswith("ap_") or c.data.startswith("re_"):
        admin(c)

# =========================
# RUN
# =========================
print("Bot running...")
bot.infinity_polling(skip_pending=True)