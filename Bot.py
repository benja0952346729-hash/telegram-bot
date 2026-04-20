import telebot
from telebot import types
import firebase_admin
from firebase_admin import credentials, db
import os, json

# =========================
# 🔐 Firebase
# =========================
cred = credentials.Certificate(json.loads(os.environ.get("FIREBASE_KEY")))
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://house-rent-app-3674a-default-rtdb.firebaseio.com/'
})

# =========================
# 🤖 BOT
# =========================
bot = telebot.TeleBot(os.environ.get("BOT_TOKEN"), parse_mode="HTML")
ADMIN_ID = 6883208728

user_data = {}

# =========================
# 🎮 MENU
# =========================
def menu(chat_id):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("50 ብር", callback_data="pay_50"),
        types.InlineKeyboardButton("100 ብር", callback_data="pay_100"),
        types.InlineKeyboardButton("200 ብር", callback_data="pay_200"),
        types.InlineKeyboardButton("300 ብር", callback_data="pay_300"),
        types.InlineKeyboardButton("500 ብር", callback_data="pay_500"),
        types.InlineKeyboardButton("1000 ብር", callback_data="pay_1000"),
        types.InlineKeyboardButton("2000 ብር", callback_data="pay_2000"),
    )
    m.add(
        types.InlineKeyboardButton("💳 ባላንስ", callback_data="bal"),
        types.InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")
    )

    bot.send_message(chat_id,
        "<b>🎮 ለመጫወት ብር ያስገቡ</b>\n\n✨ ፓኬጅ ይምረጡ 👇",
        reply_markup=m
    )

@bot.message_handler(commands=['start'])
def start(m):
    menu(m.chat.id)

# =========================
# 💳 BALANCE
# =========================
@bot.callback_query_handler(func=lambda c: c.data=="bal")
def balance(c):
    data = db.reference(f"users/{c.from_user.id}").get() or {}
    bot.send_message(c.message.chat.id, f"💰 {data.get('balance',0)} ብር")

# =========================
# 💰 PAY SELECT
# =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith("pay_"))
def pay(c):
    amt = c.data.split("_")[1]
    user_data[c.from_user.id] = {"mode":"deposit", "amount":amt}

    bot.send_message(c.message.chat.id,
        f"<b>✅ {amt} ብር መርጠዋል</b>\n\n"
        "🏦 CBE: 1000641057146\n"
        "📱 0952346729\n\n"
        "📸 screenshot ላኩ"
    )

# =========================
# 📸 PHOTO
# =========================
@bot.message_handler(content_types=['photo'])
def photo(m):

    u = user_data.get(m.from_user.id)

    if not u or u.get("mode") != "deposit":
        bot.send_message(m.chat.id,"❗ ብር አልመረጡም")
        return

    amt = u["amount"]
    file_id = m.photo[-1].file_id

    ref = db.reference("payments").push({
        "user_id": m.from_user.id,
        "amount": amt,
        "status": "pending"
    })

    pid = ref.key

    mk = types.InlineKeyboardMarkup()
    mk.add(
        types.InlineKeyboardButton("✅ Approve", callback_data=f"ok_{pid}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"no_{pid}")
    )

    bot.send_photo(ADMIN_ID, file_id, caption=f"{amt} ብር", reply_markup=mk)

    bot.send_message(
        m.chat.id,
        "⏳ ክፍያዎ በማረጋገጥ ላይ ነው\n⌛ 5 ደቂቃ ይጠብቁ"
    )

    # clear state
    user_data.pop(m.from_user.id, None)

# =========================
# ✅ APPROVE
# =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith("ok_"))
def approve(c):
    pid = c.data.split("_")[1]
    data = db.reference(f"payments/{pid}").get()

    uid = data["user_id"]
    amt = int(data["amount"])

    ref = db.reference(f"users/{uid}")
    bal = (ref.get() or {}).get("balance",0)

    ref.update({"balance": bal + amt})

    bot.send_message(uid, f"✅ {amt} ብር ገብቷል")
    bot.answer_callback_query(c.id, "Approved")

# =========================
# ❌ REJECT
# =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith("no_"))
def reject(c):
    pid = c.data.split("_")[1]
    data = db.reference(f"payments/{pid}").get()
    bot.send_message(data["user_id"], "❌ አልተቀበለም")

# =========================
# 💸 WITHDRAW START
# =========================
@bot.callback_query_handler(func=lambda c: c.data=="withdraw")
def withdraw(c):
    user_data[c.from_user.id] = {"mode":"withdraw","step":"amount"}
    bot.send_message(c.message.chat.id,"💸 ምን ያህል ብር?")

# =========================
# 💸 AMOUNT
# =========================
@bot.message_handler(func=lambda m: user_data.get(m.from_user.id,{}).get("mode")=="withdraw" and user_data[m.from_user.id].get("step")=="amount")
def w_amount(m):
    try:
        amt = int(m.text)
    except:
        bot.send_message(m.chat.id,"❗ ቁጥር ብቻ ላክ")
        return

    user_data[m.from_user.id]["amount"] = amt
    user_data[m.from_user.id]["step"] = "phone"

    bot.send_message(m.chat.id,"📱 ስልክ ቁጥር ላክ")

# =========================
# 💸 PHONE
# =========================
@bot.message_handler(func=lambda m: user_data.get(m.from_user.id,{}).get("mode")=="withdraw" and user_data[m.from_user.id].get("step")=="phone")
def w_phone(m):

    data = user_data[m.from_user.id]
    amt = data["amount"]

    ref = db.reference(f"users/{m.from_user.id}")
    bal = (ref.get() or {}).get("balance",0)

    if amt > bal:
        bot.send_message(m.chat.id,"❌ ባላንስ አነስተኛ ነው")
        user_data.pop(m.from_user.id, None)
        return

    wref = db.reference("withdraws").push({
        "user_id": m.from_user.id,
        "amount": amt,
        "phone": m.text,
        "status": "pending"
    })

    wid = wref.key

    mk = types.InlineKeyboardMarkup()
    mk.add(
        types.InlineKeyboardButton("✅ Approve", callback_data=f"wok_{wid}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"wno_{wid}")
    )

    bot.send_message(ADMIN_ID, f"💸 {amt} ብር\n📱 {m.text}", reply_markup=mk)
    bot.send_message(m.chat.id,"⏳ በማረጋገጥ ላይ ነው")

    # clear
    user_data.pop(m.from_user.id, None)

# =========================
# ✅ WITHDRAW OK
# =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith("wok_"))
def wok(c):
    wid = c.data.split("_")[1]
    data = db.reference(f"withdraws/{wid}").get()

    uid = data["user_id"]
    amt = int(data["amount"])

    ref = db.reference(f"users/{uid}")
    bal = (ref.get() or {}).get("balance",0)

    ref.update({"balance": bal - amt})

    bot.send_message(uid, f"✅ {amt} ብር ተልኳል")
    bot.answer_callback_query(c.id,"Done")

# =========================
# ❌ WITHDRAW NO
# =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith("wno_"))
def wno(c):
    wid = c.data.split("_")[1]
    data = db.reference(f"withdraws/{wid}").get()
    bot.send_message(data["user_id"],"❌ rejected")

# =========================
# RUN
# =========================
while True:
    try:
        bot.infinity_polling()
    except:
        pass
