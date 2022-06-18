import logging
import os.path
import telebot
from telebot import types
import re
import requests
from dotenv import load_dotenv
from flask import Flask, request

from vk_functions import get_id, get_list_friends, get_big_list


logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')
VK_TOKEN = os.getenv('VK_TOKEN')

bot = telebot.TeleBot(token=TELEGRAM_TOKEN)

server = Flask(__name__)

list_ids = []

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
    bot.send_message(ADMIN_ID, f'Пользователь {message.from_user.id} ({from_user_first_name} {from_user_last_name}) запустил бота', parse_mode='html')
    bot.send_message(message.chat.id, mess, parse_mode='html')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn0 = types.KeyboardButton('Узнать ID пользователя ВК')
    btn1 = types.KeyboardButton('Анализ странички ВКонтакте')
    btn2 = types.KeyboardButton('Сравнить списки друзей')
    markup.add(btn0, btn1, btn2)
    bot.send_message(message.chat.id, 'Пока я еще только учусь, так что не судите строго', reply_markup=markup)


@bot.message_handler(commands=['vk'])
def url_vk(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Перейти на vk.com', url='https://vk.com'))
    bot.send_message(message.chat.id, 'Ссылка', reply_markup=markup)


@bot.message_handler(content_types=['text'])
def funcs(message):
    if re.fullmatch(r'\d*', message.text):
        bot.send_message(ADMIN_ID,
                         f'Пользователь {message.from_user.id} запросил список друзей пользователя {message.text}',
                         parse_mode='html')
        # if os.path.exists(f'reports/{message.text}.txt'):
        #     # bot.send_message(message.chat.id, 'По этому профилю отчет уже есть. Держи.', parse_mode='html')
        #     with open(f'reports/{message.text}.txt', 'rb') as f:
        #         bot.send_document(message.chat.id, f)
        # else:
        temp_message_report = bot.send_message(message.chat.id, 'Отчет формируется. Немного подождите.', parse_mode='html')
        with open(f'reports/{message.text}.txt', 'w+', encoding='utf-8') as f:
            info2 = get_big_list(message.text)
            f.write("Расширенный список друзей пользователя\n" + info2)
        bot.delete_message(chat_id=message.chat.id, message_id=temp_message_report.id)
        with open(f'reports/{message.text}.txt', 'rb') as f:
            bot.send_document(message.chat.id, f)
    elif message.text == 'Узнать ID пользователя ВК':
        bot.send_message(ADMIN_ID,
                         f'Пользователь {message.from_user.id} хочет узнать ID пользователя {message.text}',
                         parse_mode='html')
        msg = bot.send_message(message.chat.id, 'Введи ссылку или nickname', parse_mode='html')
        bot.register_next_step_handler(msg, get_vk_id)
    elif message.text == 'Анализ странички ВКонтакте':
        bot.send_message(message.chat.id, 'Введи id пользователя\n<u>(только числовое значение)</u>', parse_mode='html')
    elif message.text == 'Сравнить списки друзей':
        global list_ids
        list_ids = []
        msg = bot.send_message(message.chat.id, 'Введи id первого пользователя\n<u>(только числовое значение)</u>', parse_mode='html')
        bot.register_next_step_handler(msg, get_first_id)
    elif message.text == 'Hello':
        bot.send_message(message.chat.id, 'Hi!', parse_mode='html')
    elif message.text == 'id':
        bot.send_message(message.chat.id, f'Твой ID: {message.from_user.id}', parse_mode='html')
    elif message.text == 'photo':
        photo = open('AnaliticNNbot.jpg', 'rb')
        bot.send_photo(message.chat.id, photo)
    else:
        bot.send_message(message.chat.id, message.text, parse_mode='html')


def get_vk_id(message):
    vk_id = get_id(message.text)
    bot.send_message(message.chat.id, vk_id, parse_mode='html')


@bot.callback_query_handler(func=lambda call: call.data == "cb_add_vkuser")
def cb_add_vkuser(call):
    bot.send_message(call.message.chat.id, 'Введите следующий id', parse_mode='html')
    bot.register_next_step_handler(call.message, get_second_id)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "cb_get_result")
def cb_get_result(call):
    global list_ids
    temp_message_report = bot.send_message(call.message.chat.id, 'Идет обработка. Немного подождите.', parse_mode='html')
    common_friends = get_list_friends(list_ids)
    if len(common_friends) == 0:
        bot.edit_message_text('Общих друзей не найдено', chat_id=call.message.chat.id, message_id=temp_message_report.id)
    else:
        msg = 'Список общих друзей:'
        for friend in common_friends:
            msg += '\nhttps://vk.com/id' + friend
        admin_msg = 'список общих друзей для:'
        for x in list_ids:
            admin_msg += '\n' + x
        bot.send_message(ADMIN_ID,
                         f'Пользователь {call.message.from_user.id} запросил {admin_msg}',
                         parse_mode='html')
        bot.edit_message_text(msg, chat_id=call.message.chat.id,
                              message_id=temp_message_report.id)
    bot.answer_callback_query(call.id)


def get_first_id(message):
    if re.fullmatch(r'\d*', message.text):
        global list_ids
        list_ids.append(message.text)
        first_message = bot.reply_to(message, f'Первый id: {message.text}. Теперь второй', parse_mode='html')
        bot.register_next_step_handler(first_message, get_second_id)
    else:
        bot.send_message(message.chat.id, f'Неправильный id', parse_mode='html')


def get_second_id(first_message):
    global list_ids
    if re.fullmatch(r'\d*', first_message.text):
        list_ids.append(first_message.text)
        msg = 'Список id для сравнения:'
        for x in list_ids:
            msg += '\n' + x
        bot.send_message(first_message.chat.id, text=msg, parse_mode='html', reply_markup=gen_markup())
    else:
        bot.send_message(first_message.chat.id, f'Неправильный id', parse_mode='html')


def gen_markup():
    markup = types.InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        types.InlineKeyboardButton("Добавить еще", callback_data="cb_add_vkuser"),
        types.InlineKeyboardButton("Сравнить", callback_data="cb_get_result")
    )
    return markup


bot.enable_save_next_step_handlers(delay=1)
bot.load_next_step_handlers()


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