from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import openai
import os
import requests
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Инициализация OpenAI API
openai.api_key = os.getenv('OPENAI_API_KEY')

# Функция для создания видео с помощью HeyGen
def create_video_with_heygen(text):
    heygen_api_url = "https://api.heygen.com/v2/video/generate"
    heygen_api_key = os.getenv('HEYGEN_API_KEY')

    data = {
        'video_inputs': [
            {
                'character': {
                    'type': 'avatar',
                    'avatar_id': 'your_avatar_id',  # Замените на ваш avatar_id
                    'avatar_style': 'normal'
                },
                'voice': {
                    'type': 'text',
                    'input_text': text,
                    'voice_id': 'your_voice_id',  # Замените на ваш voice_id
                    'speed': 1.0
                }
            }
        ],
        'test': True,
        'aspect_ratio': '16:9'
    }

    headers = {
        "Authorization": f"Bearer {heygen_api_key}",
        "Content-Type": "application/json"
    }

    response = requests.post(heygen_api_url, json=data, headers=headers)
    response_data = response.json()

    if response.status_code == 200 and "video_id" in response_data['data']:
        video_id = response_data['data']['video_id']
        return video_id
    else:
        print(f"Error creating video: {response_data}")
        return None

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
        result = response.choices[0].message.content

        # Создаем видео с помощью HeyGen
        video_id = create_video_with_heygen(result)
        if video_id:
            video_url = f'https://api.heygen.com/v2/video/{video_id}'  # Пример URL для доступа к видео
            update.message.reply_text(f'Ваше видео готово: {video_url}')
        else:
            update.message.reply_text('К сожалению, не удалось создать видео.')

        del context.user_data[user_id]

def main():
    telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    updater = Updater(telegram_bot_token, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
