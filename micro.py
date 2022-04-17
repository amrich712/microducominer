import hashlib
import os
from socket import socket
import sys  # Only python3 included libraries
import time
import requests


soc = socket()


def current_time():
    t = time.localtime()
    current_time = time.strftime("%H:%M:%S", t)
    return current_time

username = input('Введите имя пользователя\n> ')
mining_key = input("Введите майнинг ключ [Оставьте пустым, если нет ключа]\n> ")
diff_choice = input(
    'Исользовать низкую сложность? (Д/н) [Оставьте пустым для обычной сложности]\n> ')
if diff_choice.lower == "н":
    UseLowerDiff = False
else:
    UseLowerDiff = True

def fetch_pools():
    while True:
        try:
            response = requests.get(
                "https://server.duinocoin.com/getPool"
            ).json()
            NODE_ADDRESS = response["ip"]
            NODE_PORT = response["port"]

            return NODE_ADDRESS, NODE_PORT
        except Exception as e:
            print (f'{current_time()} : Ошибка подключения, переподключение через 5 секунд')
            time.sleep(5)

while True:
    try:
        print(f'{current_time()} : Поиск лучшего соединения к серверу')
        try:
            NODE_ADDRESS, NODE_PORT = fetch_pools()
        except Exception as e:
            NODE_ADDRESS = "server.duinocoin.com"
            NODE_PORT = 2813
            print(f'{current_time()} : Исользуется стандартный адрес и порт')
        soc.connect((str(NODE_ADDRESS), int(NODE_PORT)))
        print(f'{current_time()} : Соединено')
        server_version = soc.recv(100).decode()
        print (f'{current_time()} : Версия сервера: '+ server_version)
        # Начало скрипта майнинга
        while True:
            if UseLowerDiff:
                # Отправка работы при низкой сложности
                soc.send(bytes(
                    "JOB,"
                    + str(username)
                    + ",LOW,"
                    + str(mining_key),
                    encoding="utf8"))
            else:
                # Отправка работы
                soc.send(bytes(
                    "JOB,"
                    + str(username)
                    + ",MEDIUM,"
                    + str(mining_key),
                    encoding="utf8"))

            # Получение работы
            job = soc.recv(1024).decode().rstrip("\n")
            # Split received data to job and difficulty 
            job = job.split(",")
            difficulty = job[2]

            hashingStartTime = time.time()
            base_hash = hashlib.sha1(str(job[0]).encode('ascii'))
            temp_hash = None

            for result in range(100 * int(difficulty) + 1):
                # Подсчет хешрейта при сложности 
                temp_hash = base_hash.copy()
                temp_hash.update(str(result).encode('ascii'))
                ducos1 = temp_hash.hexdigest()
                
                if job[1] == ducos1:
                    hashingStopTime = time.time()
                    timeDifference = hashingStopTime - hashingStartTime
                    hashrate = result / timeDifference

                    # Отправка результата на сервер
                    soc.send(bytes(
                        str(result)
                        + ","
                        + str(hashrate)
                        + ",Minimal_PC_Miner",
                        encoding="utf8"))

                    # Получение ответа
                    feedback = soc.recv(1024).decode().rstrip("\n")
                    # Ответ положи
                    if feedback == "GOOD":
                        print(f'{current_time()} : Принято',
                              result,
                              "Хешрейт",
                              int(hashrate/1000),
                              "kH/s",
                              "Сложность:",
                              difficulty)
                        break
                    # Ответ отрицательный
                    elif feedback == "BAD":
                        print(f'{current_time()} : Отклонено',
                              result,
                              "Хешрейт",
                              int(hashrate/1000),
                              "kH/s",
                              "Сложность",
                              difficulty)
                        break

    except Exception as e:
        print(f'{current_time()} : Ошибка: ' + str(e) + ", перезапуск через 5 секунд.")
        time.sleep(5)
        os.execl(sys.executable, sys.executable, *sys.argv)