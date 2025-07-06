replyimport logging
import os
from flask import Flask, request
from telegram import Update, Bot, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Telegram bot token
TOKEN = os.environ.get("BOT_TOKEN")
bot = Bot(TOKEN)

# Flask app
app = Flask(__name__)

# Вкусы
FLAVORS = [
    "Blueberry Raspberry",
    "Dark Cherry",
    "Sakura Grape",
    "Banana Strawberry",
    "Strawberry Kiwi",
    "Watermelon Chill",
    "Fruity Chews"
]

(CHOOSING_FLAVOR, GET_NAME, GET_PHONE, GET_ADDRESS, GET_PAYMENT) = range(5)
ADMIN_USERNAME = "@sulttt2329"

def init_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("WakaOrders").sheet1
    return sheet

def save_order_to_sheet(data):
    sheet = init_gsheet()
    row = [data['name'], data['phone'], data['address'], data['flavor'], data['payment'], datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
    sheet.append_row(row)

application = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🛒 Оформить заказ"], ["📋 Посмотреть вкусы"], ["ℹ️ Информация"]]
    await update.message.reply_text(
        "Привет! Это бот WakaStore. Что хотите сделать?",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Мы продаём электронные сигареты Waka с доставкой по городу Тараз.\n"
        "Оплата Kaspi или наличными при получении."
    )

async def show_flavors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    flavors = "\n".join(f"- {f}" for f in FLAVORS)
    await update.message.reply_text(f"Доступные вкусы:\n{flavors}")

async def order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[f] for f in FLAVORS]
    await update.message.reply_text("Выберите вкус:", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return CHOOSING_FLAVOR

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['flavor'] = update.message.text
    await update.message.reply_text("Введите ваше имя:")
    return GET_NAME

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Введите номер телефона:")
    return GET_PHONE

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("Введите адрес доставки:")
    return GET_ADDRESS

async def get_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['address'] = update.message.text
    keyboard = [["Kaspi", "Наличными"]]
    await update.message.reply_text("Выберите способ оплаты:", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return GET_PAYMENT

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['payment'] = update.message.text
    data = context.user_data
    order_text = (
        "🛒 *Новый заказ:*\n\n"
        f"👤 Имя: {data['name']}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"📍 Адрес: {data['address']}\n"
        f"💨 Вкус: {data['flavor']}\n"
        f"💰 Оплата: {data['payment']}"
    )
    await update.message.reply_text("Спасибо! Ваш заказ принят.")
    await context.bot.send_message(chat_id=ADMIN_USERNAME, text=order_text, parse_mode="Markdown")
    save_order_to_sheet(data)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Заказ отменён.")
    return ConversationHandler.END

conv = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("^(🛒 Оформить заказ)$"), order)],
    states={
        CHOOSING_FLAVOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
        GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
        GET_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
        GET_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_payment)],
        GET_PAYMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_order)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.Regex("^(📋 Посмотреть вкусы)$"), show_flavors))
application.add_handler(MessageHandler(filters.Regex("^(ℹ️ Информация)$"), info))
application.add_handler(conv)

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    application.update_queue.put_nowait(update)
    return "ok"

@app.route('/')
@app.route('/healthcheck')
def healthcheck():
    return "Bot is running!"

if __name__ == '__main__':
    application.run_webhook(
        listen='0.0.0.0',
        port=int(os.environ.get("PORT", 5000)),
        webhook_url=os.environ.get("WEBHOOK_URL")
    )
