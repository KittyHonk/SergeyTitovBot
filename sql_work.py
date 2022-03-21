import pymysql
import uuid
from datetime import datetime
from pymysql.cursors import DictCursor
from contextlib import closing

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
        query = "CREATE TABLE IF NOT EXISTS Worker (RowId varchar(255), UserId int, LastName varchar(255), FirstName varchar(255), Longitude float(6), Latitude float(6), CurDateTime DATETIME, UNIQUE KEY(RowId))"
        cursor.execute(query)
        connection.commit()

def insert_in_db(id, last_name, first_name):
    #Вставка в БД имени, фамилии и айди пользователя + присвоение уникального ключа
    with connection.cursor() as cursor:
        unique_key = str(uuid.uuid4())
        query = "INSERT INTO Worker (RowId, UserId, LastName, FirstName, CurDateTime) VALUES" + "('{}', {}, '{}', '{}', '{}')".format(unique_key, id, last_name, first_name, datetime.today())
        cursor.execute(query)
        connection.commit()
        return unique_key
        
def insert_geo(unique_key, longitude, latitude):
    #Вставка в таблицу геолокации
    with connection.cursor() as cursor:      
        query = "UPDATE Worker SET Longitude = {}, Latitude = {} WHERE RowId =".format(longitude, latitude) + "'{}'".format(unique_key)
        cursor.execute(query)
        connection.commit()

#Вызов метода для создания таблицы
create_table()
