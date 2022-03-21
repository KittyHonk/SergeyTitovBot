import telebot
import sql_work
import datetime
from datetime import datetime
from telebot import types
#Токен бота
bot = telebot.TeleBot('Вставить токен сюда')


@bot.message_handler(commands=["start"])
def start(message):
    #Клавиатура с кнопками запроса
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_work_on = types.KeyboardButton(text="Пришел на работу")
    button_work_off = types.KeyboardButton(text="Ушел с работы")
    button_geo = types.KeyboardButton(text="Отправить местоположение", request_location=True)
    keyboard.add(button_work_on)
    keyboard.add(button_work_off)
    keyboard.add(button_geo)
    bot.send_message(message.chat.id, "Выбери опцию", reply_markup=keyboard)


@bot.message_handler(content_types=['text', 'location'])
def work_option(message):
    #Логика выхода/ухода с работы
    if message.text == "Пришел на работу":
        bot.send_message(message.chat.id, "Рабочий день начался, отправь геолокацию")
        bot.register_next_step_handler(message, location);
    elif message.text == "Ушел с работы":
        bot.send_message(message.chat.id, "Рабочий день закончился, отправь геолокацию")  
        bot.register_next_step_handler(message, location);
    else: 
        bot.send_message(message.chat.id, "Неизвестная команда, попробуй еще раз")
        start(message)
    
    
def location(message):
    #Логика снятия геолокации + проверка на forward
    if message.location is not None and message.forward_from is None:
        bot.send_message(message.chat.id, "Геолокация получена")
        unique_key = sql_work.insert_in_db(message.from_user.id, message.from_user.last_name, message.from_user.first_name)
        sql_work.insert_geo(unique_key, message.location.longitude, message.location.latitude)
    else:
        bot.send_message(message.chat.id, "Геолокация не получена, начни/заверши рабочий день еще раз")
        start(message)

#Запросы на изменения от бота, можно настроить interval, в случае ошибки пропускает тик запроса
try: 
    bot.polling(none_stop=True, interval=0)
except Exception:
    pass