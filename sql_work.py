from concurrent.futures import process
from sqlite3 import connect
import pymysql
import uuid
from datetime import datetime
from datetime import timedelta
from pymysql.cursors import DictCursor

#Тут настраивается подключение к БД
connection = pymysql.connect(
    host='localhost', #Хост БД
    user='root', #Пользователь, требуется с доступом на изменение таблиц
    password='admin', #Пароль пользователя
    db='pytest', #БД для подключения
    charset='utf8mb4', #Кодировка БД, стоит по умолчанию для MySQL
    cursorclass=DictCursor
)   

def create_table():
    #Создание таблицы в случае её отсутствия
    with connection.cursor() as cursor:      
        query = "CREATE TABLE IF NOT EXISTS WorkerNew (RowId varchar(255), UserId int, LastName varchar(255), FirstName varchar(255), LongitudeIn float(6), LatitudeIn float(6), DateTimeIn DATETIME, LongitudeOut float(6), LatitudeOut float(6), DateTimeOut DATETIME, DiffTime varchar(255), CurWork int, AlreadyCheck int, UNIQUE KEY(RowId))"
        cursor.execute(query)
        connection.commit()
        
def create_table_timeCheck():
    #Создание таблицы учета времени переработок
    with connection.cursor() as cursor:      
        query = "CREATE TABLE IF NOT EXISTS Processing (RowId varchar(255), UserId int, LastName varchar(255), FirstName varchar(255), DateTimeProcessing float(6), UNIQUE KEY(RowId))"
        cursor.execute(query)
        connection.commit()
        
def create_scheduler():
    #Создание регулярной очистки ночью столбца AlreadyCheck через Schedule MySQL
    with connection.cursor() as cursor:
        query = "set global event_scheduler = on"
        cursor.execute(query)
        connection.commit()
        query = "CREATE EVENT new_day ON SCHEDULE EVERY 1 DAY STARTS '2022-04-06 21:00:01.000' ON COMPLETION NOT PRESERVE ENABLE DO update WorkerNew set AlreadyCheck = 0 where AlreadyCheck = 1"
        try:
            cursor.execute(query)
        except:
            pass
        connection.commit()
        
def resetalreadycheck():
    #Функция сброса AlreadyCheck
    with connection.cursor() as cursor:
        query = "UPDATE WorkerNew set AlreadyCheck = 0 WHERE AlreadyCheck = 1"
        cursor.execute(query)
        connection.commit()
        
def insert_in_processing_db(id, last_name, first_name, processing_time):
    #Вставка в БД по учету переработок: имени, фамилии, айди, в случае отсутсвия - создание такой строки
    with connection.cursor() as cursor:
        unique_key = str(uuid.uuid4())
        query = "SELECT * FROM Processing WHERE UserId = {}".format(id)
        cursor.execute(query)
        check = cursor.fetchall()
        if (check == ()):
            query = "INSERT INTO Processing (RowId, UserId, LastName, FirstName) VALUES" + "('{}', {}, '{}', '{}')".format(unique_key, id, last_name, first_name)
            cursor.execute(query)
            connection.commit()
        delta = processing_time
        minutes = round(delta.seconds/60, 2)
        hours = round(minutes/60, 2)
        if hours >= 8:
            hours -= 8;
            query = "UPDATE Processing SET DateTimeProcessing = {} WHERE UserId = {}".format(hours, id)
            cursor.execute(query)
            connection.commit()
        connection.commit()

def check_processing_time(id):
    with connection.cursor() as cursor:
        query = "SELECT DateTimeProcessing FROM Processing WHERE UserId = {}".format(id)
        cursor.execute(query)
        check = cursor.fetchall()
        return check

def get_holiday(id):
    with connection.cursor() as cursor:
        query = "SELECT DateTimeProcessing FROM Processing WHERE UserId = {}".format(id)
        cursor.execute(query)
        check = cursor.fetchall()
        check = check[0]['DateTimeProcessing']
        if (check >= 8):
            check -= 8
            query = "UPDATE Processing SET DateTimeProcessing = {} WHERE UserId = {}".format(check, id)
            cursor.execute(query)
            connection.commit()
            return "Выходной взят"
        else:
            return "Выходной не взят, недостаточно часов на балансе"
        

def insert_in_db(id, last_name, first_name):
    #Вставка в БД имени, фамилии и айди пользователя + присвоение уникального ключа
    with connection.cursor() as cursor:
        unique_key = str(uuid.uuid4())
        query = "INSERT INTO WorkerNew (RowId, UserId, LastName, FirstName, DateTimeIn, CurWork, AlreadyCheck) VALUES" + "('{}', {}, '{}', '{}', '{}', {}, {})".format(unique_key, id, last_name, first_name, datetime.today(), 1, 1)
        cursor.execute(query)
        connection.commit()
        return unique_key

def insert_geo(unique_key, longitude, latitude):
    #Вставка в таблицу геолокации
    with connection.cursor() as cursor:      
        query = "UPDATE WorkerNew SET LongitudeIn = {}, LatitudeIn = {} WHERE RowId =".format(longitude, latitude) + "'{}'".format(unique_key)
        cursor.execute(query)
        connection.commit()

def update_in_db(userid, longitude, latitude):
    #Обновление информации о пользователе
    with connection.cursor() as cursor:
        query = "UPDATE WorkerNew SET LongitudeOut = {}, LatitudeOut = {}, ".format(longitude, latitude) + "DateTimeOut = " + "'{}' ".format(datetime.today()) + "WHERE UserId = '{}' and CurWork = 1".format(userid)
        cursor.execute(query)
        connection.commit()

def check_for_worknow(userid):
    #Проверка на состояние работника
    with connection.cursor() as cursor:
        curWork = None
        alreadyCheck = None
        query = "SELECT * FROM WorkerNew WHERE CurWork = 1 and UserId = {}".format(userid)
        curWork = cursor.execute(query)
        query = "SELECT AlreadyCheck FROM WorkerNew WHERE AlreadyCheck = 1 and UserId = {}".format(userid)
        cursor.execute(query)
        alreadyCheck = cursor.fetchall()
        check = False
        for i in range(len(alreadyCheck)):
            if alreadyCheck[i]['AlreadyCheck'] == 1:
                check = True
        connection.commit()
        return curWork, check

def difftime(userid):
    #Вычисление отработаного времени
    with connection.cursor() as cursor:
        query = "SELECT DateTimeIn, DateTimeOut FROM WorkerNew WHERE CurWork = 1 and UserId = " + "'{}'".format(userid)
        cursor.execute(query)
        worktime = cursor.fetchall()
        w1 = worktime[0]['DateTimeIn']
        w2 = worktime[0]['DateTimeOut']
        tdelta = w2 - w1
        minutes = round(tdelta.seconds/60, 2)
        hours = round(minutes/60, 2)
        query = "UPDATE WorkerNew SET CurWork = 0, DiffTime = " + "'{}'".format(hours) + " WHERE CurWork = 1 and UserId = " + "{}".format(userid)
        cursor.execute(query)
        connection.commit()
        return tdelta
    
def get_statistic():
    #Вывод общей статистики по отработаному времени
    with connection.cursor() as cursor:
        today = datetime.today()
        year = today.year - 3
        month = today.month
        day = today.day
        delta = monthdelta(datetime(year, month, day), -1)
        query = "SELECT LastName, FirstName, sum(DiffTime) FROM WorkerNew WHERE DateTimeIn >= " + "'{}'".format(delta) + " GROUP BY FirstName"
        cursor.execute(query)
        return (cursor.fetchall())
        
def monthdelta(date, delta):
    m, y = (date.month+delta) % 12, date.year + ((date.month)+delta-1)
    if not m: m = 12
    d = min(date.day, [31,
        29 if y%4==0 and (not y%100==0 or y%400 == 0) else 28,
        31,30,31,30,31,31,30,31,30,31][m-1])
    return date.replace(day=d,month=m, year=y)    

def new_day():
    #Обнуление столбца AlreadyCheck отвечающего за возможность отметки за текущий день
    with connection.cursor() as cursor:
        query = "UPDATE WorkerNew SET AlreadyCheck = 0"
        cursor.execute(query)
        connection.commit()
        
#Вызов метода для создания таблицы
create_table()
create_table_timeCheck()
create_scheduler()
