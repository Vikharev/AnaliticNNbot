import os.path
import telebot
from telebot import types
import re
import requests
from dotenv import load_dotenv
from flask import Flask, request

from vk_functions import get_big_list

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

bot = telebot.TeleBot(token=TELEGRAM_TOKEN)

server = Flask(__name__)


@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.first_name is not None:
        from_user_first_name = message.from_user.first_name
    else:
        from_user_first_name = ''
    if message.from_user.last_name is not None:
        from_user_last_name = message.from_user.last_name
    else:
        from_user_last_name = ''
    mess = f'Привет, <b>{from_user_first_name} {from_user_last_name}</b>!\n Чем помочь?'
    bot.send_message(message.chat.id, mess, parse_mode='html')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton('Анализ странички ВКонтакте')
    btn2 = types.KeyboardButton('Пока еще посто бесполезная кнопка')
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, 'Пока я еще только учусь, так что не судите строго', reply_markup=markup)


@bot.message_handler(commands=['vk'])
def url_vk(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Перейти на vk.com', url='https://vk.com'))
    bot.send_message(message.chat.id, 'Ссылка', reply_markup=markup)


@bot.message_handler(content_types=['text'])
def funcs(message):
    if re.fullmatch(r'\d*', message.text):
        if os.path.exists(f'reports/{message.text}.txt'):
            bot.send_message(message.chat.id, 'По этому профилю отчет уже есть. Держи.', parse_mode='html')
            f = open(f'reports/{message.text}.txt', 'rb')
            bot.send_document(message.chat.id, f)
        else:
            temp_message_report = bot.send_message(message.chat.id, 'Отчет формируется. Немного подождите.', parse_mode='html')
            with open(f'reports/{message.text}.txt', 'w+', encoding='utf-8') as f:
                info2 = get_big_list(message.text)
                f.write("Расширенный список друзей пользователя\n" + info2)
            f = open(f'reports/{message.text}.txt', 'rb')
            bot.delete_message(chat_id=message.chat.id, message_id=temp_message_report.id)
            bot.send_document(message.chat.id, f)

    elif message.text == 'Анализ странички ВКонтакте':
        bot.send_message(message.chat.id, 'Введи id пользователя\n<u>(только числовое значение)</u>', parse_mode='html')
    elif message.text == 'Сравнить списки друзей':
        bot.send_message(message.chat.id, 'Введи id первого пользователя\n<u>(только числовое значение)</u>', parse_mode='html')
        bot.register_next_step_handler(message, get_first_id)
    elif message.text == 'Hello':
        bot.send_message(message.chat.id, 'Hi!', parse_mode='html')
    elif message.text == 'id':
        bot.send_message(message.chat.id, f'Твой ID: {message.from_user.id}', parse_mode='html')
    elif message.text == 'photo':
        photo = open('AnaliticNNbot.jpg', 'rb')
        bot.send_photo(message.chat.id, photo)
    else:
        bot.send_message(message.chat.id, message.text, parse_mode='html')


def get_first_id(message):
    bot.send_message(message.chat.id, f'Первый юзер: {message.text}', parse_mode='html')


@server.route('/bot', methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://analiticnnbot.herokuapp.com/bot')
    return "!", 200


if __name__ == '__main__':
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))