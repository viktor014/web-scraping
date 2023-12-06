import math
import sys
import urllib
import requests
import json
import MySQLdb
import re

# Ввод координат пользователем широты,долготы и радиуса поиска знаков ДТП

c_s = float(input('Введите координаты ДТП по широте:'))
c_d = float(input('Введите координаты ДТП по долготе:'))
r = int(input('Введите радиус для поиска знаков, м:'))

# Перевод координатов из градусов в градусы/минуты/секунды

c_sg = int(c_s)  # Преобразование, для отделения целой части, в будущем- градусы координат по широте
c_dg = int(c_d)  # Преобразование, для отделения целой части, в будущем- градусы координат по долготе
c_sm = (c_s - c_sg) * 60
c_dm = (c_d - c_dg) * 60
c_sp = int(c_sm)  # Получение минут по широте
c_dp = int(c_dm)  # Получение минут по долготе
c_ss = round((c_sm - c_sp) * 60, 1)  # Подучение секунд по широте
c_ds = round((c_dm - c_dp) * 60, 1)  # Подучение секунд по долготе
c_s2 = math.radians(c_s)  # перевод координат по широте из градусов в радианы
c_d2 = math.radians(c_d)  # перевод координат по долготе из градусов в радианы

mvs = math.cos(c_s2) * 30.92  # Количесво метров в 1 секунде по широте в зависимости от географического расположения
mvs1 = math.cos(c_d2) * 30.87  # Количество метров в 1 секунде по долготе в зависимости от географического расположения

per = round(r / mvs, 1)  # Получение значения для смещения координат по широте
per1 = round(r / mvs1, 1)  # Получение значения для смещения координат по широте

# Получение координат левой нижней точки отправляемого запроса

if ((c_ss - per) < 0):
    c_sp1 = c_sp - 1  # Получение результатов минут для левой нижней точке по широте
    c_ss1 = 60 + c_ss - per  # Получение результатов секунд для левой нижней точке по широте
else:
    c_sp1 = c_sp  # Получение результатов минут для левой нижней точке по широте
    c_ss1 = c_ss - per  # Получение результатов секунд для левой нижней точке по широте

if ((c_ds + per1) < 0):
    c_dp1 = c_dp - 1  # Получение результатов минут для левой нижней точке по долготе
    c_ds1 = 60 + c_ds - per1  # Получение результатов секунд для левой нижней точке по долготе
else:
    c_dp1 = c_dp  # Получение результатов минут для левой нижней точке по долготе
    c_ds1 = c_ds - per1  # Получение результатов секунд для левой нижней точке по долготе

# Получение координат правой верхней точки отправляемого запроса

if ((c_ss + per) > 60):
    c_sp2 = c_sp + 1  # Получение результатов минут для правой верхней точке по широте
    c_ss2 = c_ss + per - 60  # Получение результатов секунд для правой верхней точке по широте
else:
    c_sp2 = c_sp  # Получение результатов минут для правой верхней точке по широте
    c_ss2 = c_ss + per  # Получение результатов секунд для правой верхней точке по широте

if ((c_ds - per1) > 60):
    c_dp2 = c_dp + 1  # Получение результатов минут для правой верхней точке по долготе
    c_ds2 = c_ds + per1 - 60  # Получение результатов секунд для правой верхней точке по долготе
else:
    c_dp2 = c_dp  # Получение результатов минут для правой верхней точке по долготе
    c_ds2 = c_ds + per1  # Получение результатов секунд для правой верхней точке по долготе

# Перевод в обратные координаты
# Левой нижней точки

c_spi = c_sp1 / 60
c_ssi = c_ss1 / 3600
c_spi1 = c_dp1 / 60
c_ssi1 = c_ds1 / 3600

coor1 = round((c_sg + c_spi + c_ssi), 14)  # Передаваемая 1 координата по широте
coor2 = round((c_dg + c_spi1 + c_ssi1), 14)  # Передаваемая 1 координата по долготе

# Правой верхней точки

c_spi21 = c_sp2 / 60
c_ssi21 = c_ss2 / 3600
c_spi22 = c_dp2 / 60
c_ssi22 = c_ds2 / 3600

coor11 = round((c_sg + c_spi21 + c_ssi21), 14)  # Передаваемая 2 координата по широте
coor21 = round((c_dg + c_spi22 + c_ssi22), 14)  # Передаваемая 2 координата по долготе

# Отправка POST-запроса на сайт

payload = {'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br',
           'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7', 'Connection': 'keep-alive',
           'Content-Type': 'application/json',
           'Host': 'signsign.ru',
           'Origin': 'http://signsign.ru', 'Referer': 'http://signsign.ru/'}
para = {'bounds': [[coor1, coor2], [coor11, coor21]]}
try:
    r = requests.post("https://signsign.ru/api/2.0/get", headers=payload, data=json.dumps(para))
except Exception:
    print('Error!!!')
    print(sys.exc_info()[1])

tex = str(r.text)  # Занесение содержимого ответа в переменную
p = re.compile(r'<.*?>')
da = p.sub('', tex)  # Удаление html- тегов из ответа
tex2 = json.loads(da, encoding='utf-8')  # Преобразование ответа в ассоциативный массив для занесения в БД

# Подключение к БД

conn = MySQLdb.connect('localhost', 'root', '', 'CoordsDB', charset='utf8')
cursor = conn.cursor()

# cursor.execute("SELECT * FROM Crash")
cursor.execute("INSERT INTO Crash(latitude_crash,longitude_crash) VALUES(%s,%s)", (c_s, c_d))
id_1 = conn.insert_id()
conn.commit()

for val in tex2['result']:
    cursor.execute("INSERT INTO Sign (name_sign,coord_latitude,coord_longitude,description) VALUES (%s,%s,%s,%s)",
                   (val['title'], val['coords']['lat'], val['coords']['lon'], val['description']))
    id_2 = conn.insert_id()
    conn.commit()
    cursor.execute("INSERT INTO Connect (id_sign,id_crashs) VALUES (%s,%s)", (id_1, id_2))
conn.commit()

conn.close()