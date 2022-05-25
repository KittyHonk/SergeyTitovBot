import telebot
import sql_work
from datetime import datetime
from telebot import types
#Токен бота
bot = telebot.TeleBot('')

@bot.message_handler(commands=["start"])
def start(message):
    #Клавиатура с кнопками запроса
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_work_on = types.KeyboardButton(text="Пришел на работу")
    button_work_off = types.KeyboardButton(text="Ушел с работы")
    button_geo = types.KeyboardButton(text="Отправить местоположение", request_location=True)
    button_processing = types.KeyboardButton(text="Учет переработок")
    button_statistic = types.KeyboardButton(text="Статистика за последний месяц")
    keyboard.add(button_work_on)
    keyboard.add(button_work_off)
    keyboard.add(button_geo)
    keyboard.add(button_processing)
    keyboard.add(button_statistic)
    bot.send_message(message.chat.id, "Выбери опцию", reply_markup=keyboard)

@bot.message_handler(commands=["resetalreadycheck"])
def resetalreadycheck(message):
    #Экстренное обнуление столбца AlreadyCheck
    sql_work.resetalreadycheck()
    bot.send_message(message.chat.id, "Сброшено")
    start(message)
    
@bot.message_handler(content_types=['text', 'location'])
def work_option(message):
    curWork, check = sql_work.check_for_worknow(message.from_user.id)
    if curWork == 0:
        worknow = False
    else:
        worknow = True
    #Логика выхода/ухода с работы + учет времени
    if message.text == "Пришел на работу":
        if worknow is False and check is False:
            bot.send_message(message.chat.id, "Рабочий день начался, отправь геолокацию")
            bot.register_next_step_handler(message, locationIn);
        elif worknow is True and check is True: 
            bot.send_message(message.chat.id, "Рабочий день уже начат")
        elif worknow is False and check is True:
            bot.send_message(message.chat.id, "Сегодня уже отмечался")
    elif message.text == "Ушел с работы":
        if worknow is True:
            bot.send_message(message.chat.id, "Рабочий день закончился, отправь геолокацию")  
            bot.register_next_step_handler(message, locationOut);
        else:
            bot.send_message(message.chat.id, "Рабочий день уже закончен / не начат")
    elif message.text == "Учет переработок":
        processing(message)
    elif message.text == "Вернуться":
        start(message)
    elif message.text == "Взять выходной":
        reply = sql_work.get_holiday(message.from_user.id)
        bot.send_message(message.chat.id, "{}".format(reply))
        start(message)
    elif message.text == "Статистика за последний месяц":
        reply = sql_work.get_statistic()
        for i in range(len(reply)):
            hours = reply[i]['sum(DiffTime)']
            day = 0
            while (hours >= 24):
                day += 1
                hours -= 24
            bot.send_message(message.chat.id, "Фамилия: {}\nИмя: {}\nДней: {}\nЧасов: {}\n".format(
                reply[i]['LastName'], reply[i]['FirstName'], day, hours
                ))
        start(message)
    else: 
        bot.send_message(message.chat.id, "Неизвестная команда, попробуй еще раз")
        start(message)

def locationIn(message):
    #Логика снятия геолокации + проверка на forward
    if message.location is not None and message.forward_from is None:
        bot.send_message(message.chat.id, "Геолокация получена")
        unique_key = sql_work.insert_in_db(message.from_user.id, message.from_user.last_name, message.from_user.first_name)
        sql_work.insert_geo(unique_key, message.location.longitude, message.location.latitude)
    else:
        bot.send_message(message.chat.id, "Геолокация не получена, начни/заверши рабочий день еще раз")
        start(message)
        
def locationOut(message):
    #Тоже самое что и locationIn + вычисление времени дельты времени работы
    if message.location is not None and message.forward_from is None:
        bot.send_message(message.chat.id, "Геолокация получена")
        sql_work.update_in_db(message.from_user.id, message.location.longitude, message.location.latitude)
        tdelta = sql_work.difftime(message.from_user.id)
        sql_work.insert_in_processing_db(message.from_user.id, message.from_user.last_name, message.from_user.first_name, tdelta)
    else:
        bot.send_message(message.chat.id, "Геолокация не получена, начни/заверши рабочий день еще раз")
        start(message)

def processing(message):
    #Вывод количества часов переработок
    processing_time = sql_work.check_processing_time(message.from_user.id)
    bot.send_message(message.chat.id, "На текущий момент часов на балансе: {}".format(processing_time[0]['DateTimeProcessing']))
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_work_on = types.KeyboardButton(text="Взять выходной")
    button_work_off = types.KeyboardButton(text="Вернуться")
    keyboard.add(button_work_on)
    keyboard.add(button_work_off)
    bot.send_message(message.chat.id, "Выбери опцию", reply_markup=keyboard)

#Запросы на изменения от бота, можно настроить interval, в случае ошибки пропускает тик запроса
if __name__ == '__main__':
    try:
        bot.polling()
    except Exception:
        pass
