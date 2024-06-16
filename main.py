from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import openai
import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Инициализация OpenAI API
openai.api_key = os.getenv('OPENAI_API_KEY')

def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Оплатить 150 рублей", callback_data='pay')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Добро пожаловать в нашего бота Астролога-Таролога! Для того чтобы получить персональную расстановку, вам нужно пополнить счет на 150 рублей.', reply_markup=reply_markup)

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    if query.data == 'pay':
        query.edit_message_text('Ваш платеж успешно принят! Спасибо. Пожалуйста, введите свои данные для персональной расстановки.\n1. Ваше имя\n2. Дата рождения (ДД-ММ-ГГГГ)\n3. Ваш знак зодиака (если известен)\n4. Вопрос или область, на которую вы хотите получить ответ')

def handle_message(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text
    user_id = update.message.from_user.id

    if user_id not in context.user_data:
        context.user_data[user_id] = {}

    if "name" not in context.user_data[user_id]:
        context.user_data[user_id]["name"] = user_input
        update.message.reply_text('Введите вашу дату рождения (ДД-ММ-ГГГГ)')
    elif "dob" not in context.user_data[user_id]:
        context.user_data[user_id]["dob"] = user_input
        update.message.reply_text('Введите ваш знак зодиака (если известен)')
    elif "zodiac" not in context.user_data[user_id]:
        context.user_data[user_id]["zodiac"] = user_input
        update.message.reply_text('Введите вопрос или область, на которую вы хотите получить ответ')
    else:
        context.user_data[user_id]["question"] = user_input
        user_data = context.user_data[user_id]
        name = user_data["name"]
        dob = user_data["dob"]
        zodiac = user_data["zodiac"]
        question = user_data["question"]

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Создай таро-расклад для пользователя с именем {name}, датой рождения {dob}, знаком зодиака {zodiac}. Вопрос: {question}"}
            ]
        )
        result = response['choices'][0]['message']['content']
        update.message.reply_text(result)
        del context.user_data[user_id]

def main():
    telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    updater = Updater(telegram_bot_token, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
