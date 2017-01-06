import botan as botan
import re
import threading

import bs4
import cherrypy
import requests
import telebot
import time

from telebot.apihelper import ApiException

from config import *
from database.SQLigter import SQLighter


bot = telebot.TeleBot(bot_token)


class WebhookServer(object):
    @cherrypy.expose
    def index(self):
        length = int(cherrypy.request.headers['content-length'])
        json_string = cherrypy.request.body.read(length)
        json_string = json_string.decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        if update.message:
            bot.process_new_messages([update.message])
        if update.inline_query:
            bot.process_new_inline_query([update.inline_query])
        return ''


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    chat_id, command, first_name, last_name, full_name, username = get_user_data(message)
    bot.send_message(chat_id, 'Введіть трек номер та, по бажанню, його опис (наприклад: RF293948577CH Телефон)'
                              ' і, як тільки статус вашої посилки буде змінено, я буду вас сповіщати. Майте на'
                              ' увазі, що я відстежую відправлення тільки по території України. \n\nПобажання'
                              ' та зауваження пишіть @ahtutejlo \n\nЯкщо бот вам сподобався - я буду вдячний, '
                              'якщо ви дасте відгук - https://telegram.me/storebot?start=ukrpostbot')
    botan.track(botan_token, chat_id, message, command)


@bot.message_handler(func=lambda message: len(message.text) < 13)
def on_short_message(message):
    chat_id, command, first_name, last_name, full_name, username = get_user_data(message)
    bot.send_message(chat_id, 'Введіть корректний трек номер.')
    botan.track(botan_token, chat_id, message, 'Incorrect track')


@bot.message_handler(func=lambda message: len(message.text) > 14)
def on_track_and_description(message):
    chat_id, command, first_name, last_name, full_name, username = get_user_data(message)
    command = message.text.split(' ')  # track number [0], description[1:]
    answer = check_track(command[0])
    description = ' '.join(command[1:])
    bot.send_message(message.chat.id, answer + '\n Я вас повідомлю, як тільки будуть оновлення по вашому відправленню.')
    db = SQLighter(db_name)
    db.insert_new_track(chat_id, command[0], answer, first_name, description)
    db.close()
    botan.track(botan_token, chat_id, message, 'Track and description')


@bot.message_handler(func=lambda message: len(message.text) == 13)
def on_track_only(message):
    chat_id, command, first_name, last_name, full_name, username = get_user_data(message)
    answer = check_track(command)
    bot.send_message(chat_id, answer + '\n Я вас повідомлю, як тільки будуть оновлення по вашому відправленню.')
    db = SQLighter(db_name)
    db.insert_new_track(chat_id, command, answer, first_name, '')
    db.close()
    botan.track(botan_token, chat_id, message, 'Track only')


def check_track(barcode):
    guid = 'fcc8d9e1-b6f9-438f-9ac8-b67ab44391dd'
    culture = 'uk'
    url = 'http://services.ukrposhta.ua/barcodestatistic/barcodestatistic.asmx/GetBarcodeInfo?guid=' + guid + \
          '&barcode=' + barcode + '&culture=' + culture
    r = requests.get(url)
    soup = bs4.BeautifulSoup(r.text, 'html.parser')
    try:
        event = bs4.BeautifulSoup(str(soup.select('eventdescription')[0]), 'html.parser').get_text()
    except IndexError as e:
        logger.error(e)
        return u"Щось пішло не так. Я повідомлю як все стане добре."
    return re.sub("^\s+|\n|\r|\s+$", '', event)


def get_user_data(msg):
    chat_id = msg.chat.id
    command = msg.text
    first_name = msg.chat.first_name
    try:
        last_name = ' ' + msg.chat.last_name
    except:
        last_name = ''
    full_name = first_name + last_name
    try:
        username = msg.chat.username
    except:
        username = 'No username'
    logger.debug('Got command: {}'.format(command))
    logger.debug('From: {}'.format(full_name))
    logger.debug('Username: {}'.format(username))
    return chat_id, command, first_name, last_name, full_name, username


def check_new_status():
    while 1:
        db = SQLighter(db_name)
        logger.debug('Checking difference...')
        for row in db.get_all():  # (id[0], chat_id[1], track[2], status[3], description[4], user_name[5])
            try:
                status = check_track(row[2])
            except TimeoutError as te:
                logger.error(te)
            if status == "Щось пішло не так. Я повідомлю як все стане добре.":
                pass
            elif status != row[3]:
                db.update_status(status, row[1], row[2])
                message = "Привіт, " + row[5] + "! Є оновлення по вашому трек номеру " + row[2] + ' ' + row[4] + \
                          "\n\nНовий статус:\n" + status
                try:
                    bot.send_message(row[1], message)
                    logger.debug('Id: ' + str(row[0]) + '. Message with new status has been sent.')
                except ApiException as e:
                    logger.warn(e)
            # else:
            #     logger.debug('Id: ' + str(row[0]) + '. No differences found.')
        logger.debug('Checking completed.')
        db.close()
        time.sleep(60 * 60)  # check every hour


th = threading.Thread(target=check_new_status, args=[], daemon=True)
th.start()

# bot.polling(none_stop=True)
if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook('https://telegram.in.ua/ukrposhta_bot/')
    cherrypy.config.update({
        'server.socket_host': '127.0.0.1',
        'server.socket_port': 7773,
        'engine.autoreload.on': False
    })
    cherrypy.quickstart(WebhookServer(), '/', {'/': {}})