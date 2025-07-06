
import logging
import os

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# Настройка логирования
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Стартовая команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["Blueberry Raspberry", "Dark Cherry"],
        ["Sakura Grape", "Banana Strawberry"],
        ["Strawberry Kiwi", "Watermelon Chill"],
        ["Fruity Chews"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Выберите вкус:", reply_markup=reply_markup)

# Обработка выбора вкуса и предложения оплаты
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text in [
        "Blueberry Raspberry", "Dark Cherry", "Sakura Grape",
        "Banana Strawberry", "Strawberry Kiwi", "Watermelon Chill", "Fruity Chews"
    ]:
        payment_keyboard = [["Kaspi", "Наличными"]]
        payment_markup = ReplyKeyboardMarkup(payment_keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("Выберите способ оплаты:", reply_markup=payment_markup)
    elif text in ["Kaspi", "Наличными"]:
        await update.message.reply_text("Спасибо за заказ! Мы скоро с вами свяжемся.")
    else:
        await update.message.reply_text("Пожалуйста, выберите пункт из меню.")

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Webhook-запуск
    webhook_url = os.environ.get("WEBHOOK_URL")
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=webhook_url,
    )

if __name__ == "__main__":
    main()
