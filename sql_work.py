import pymysql
import uuid
from datetime import datetime
from pymysql.cursors import DictCursor

#Тут настраивается подключение к БД
connection = pymysql.connect(
    host='localhost', #Хост БД
    user='root', #Пользователь, требуется с доступом на изменение таблиц
    password='admin', #Пароль пользователя
    db='pyTest', #БД для подключения
    charset='utf8mb4', #Кодировка БД, стоит по умолчанию для MySQL
    cursorclass=DictCursor
)   

def create_table():
    #Создание таблицы в случае её отсутствия
    with connection.cursor() as cursor:      
        query = "CREATE TABLE IF NOT EXISTS WorkerNew (RowId varchar(255), UserId int, LastName varchar(255), FirstName varchar(255), LongitudeIn float(6), LatitudeIn float(6), DateTimeIn DATETIME, LongitudeOut float(6), LatitudeOut float(6), DateTimeOut DATETIME, DiffTime varchar(255), CurWork int, AlreadyCheck int, UNIQUE KEY(RowId))"
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
        print(alreadyCheck)
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
        for i in range(len(worktime)):
            w1 = worktime[i]['DateTimeIn']
            w2 = worktime[i]['DateTimeOut']
            tdelta = w2 - w1
            query = "UPDATE WorkerNew SET CurWork = 0, DiffTime = " + "'{}'".format(tdelta) + " WHERE CurWork = 1 and UserId = " + "{}".format(userid)
            cursor.execute(query)
            connection.commit()

def new_day():
    #Обнуление столбца AlreadyCheck отвечающего за возможность отметки за текущий день
    with connection.cursor() as cursor:
        query = "UPDATE WorkerNew SET AlreadyCheck = 0"
        cursor.execute(query)
        connection.commit()
        print('AlreadyCheck is null')
        
#Вызов метода для создания таблицы
create_table()
create_scheduler()

