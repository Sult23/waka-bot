import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes

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

# Этапы диалога
(CHOOSING_FLAVOR, GET_NAME, GET_PHONE, GET_ADDRESS, GET_PAYMENT) = range(5)

# Админ для уведомлений
ADMIN_USERNAME = "@sulttt2329"

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🛒 Оформить заказ"], ["📋 Посмотреть вкусы"], ["ℹ️ Информация"]]
    await update.message.reply_text(
        "Привет! Это бот WakaStore. Что хотите сделать?",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Мы продаём электронные сигареты Waka с доставкой по городу Тараз.
"
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
    await update.message.reply_text("Введите ваше имя:", reply_markup=ReplyKeyboardRemove())
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
        "🛒 *Новый заказ:*

"
        f"👤 Имя: {data['name']}
"
        f"📞 Телефон: {data['phone']}
"
        f"📍 Адрес: {data['address']}
"
        f"💨 Вкус: {data['flavor']}
"
        f"💰 Оплата: {data['payment']}"
    )
    await update.message.reply_text("Спасибо! Ваш заказ принят.")
    await context.bot.send_message(chat_id=ADMIN_USERNAME, text=order_text, parse_mode="Markdown")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Заказ отменён.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    import os
    TOKEN = os.environ.get("BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

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

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^(📋 Посмотреть вкусы)$"), show_flavors))
    app.add_handler(MessageHandler(filters.Regex("^(ℹ️ Информация)$"), info))
    app.add_handler(conv)

    app.run_polling()

if __name__ == "__main__":
    main()
