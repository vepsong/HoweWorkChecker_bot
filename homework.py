import logging
import os
import time

from dotenv import load_dotenv
import requests
import telegram


logging.basicConfig(
    level=logging.DEBUG,
    filename='homework_bot.log',
    filemode='w',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


def check_tokens():
    """Сhecking env variables."""
    list = {
        PRACTICUM_TOKEN: 'PRACTICUM_TOKEN',
        TELEGRAM_TOKEN: 'TELEGRAM_TOKEN',
        TELEGRAM_CHAT_ID: 'TELEGRAM_CHAT_ID'
    }

    if all(list):
        return True

    for i in list:
        if i is None:
            logging.error(f"Отсутствует переменная окружения {list[i]}")
            return False


RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Функция отправки сообщений."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info('Отправили сообщение')
    except Exception as error:
        logging.error(f"Не смогли отправить сообщение: {error}")
        raise error


def get_api_answer(current_timestamp):
    """Получаем api-ответ от сервера Yandex."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    # params = {'from_date': 0}

    logging.info('Отправляем api-запрос')
    response = requests.get(
        ENDPOINT,
        params=params,
        headers=HEADERS,
    )

    if response.status_code != requests.codes.ok:
        if response.status_code == requests.codes.bad_request:
            logging.error('Ошибка 400')
            raise TypeError('Ошибка 400')
        elif response.status_code == requests.codes.unauthorized:
            logging.error('Ошибка 401')
            raise TypeError('Ошибка 401')
        else:
            logging.error('Проблемы соединения с сервером')
            raise TypeError('Проблемы соединения с сервером')
    elif response.status_code == requests.codes.ok:
        return response.json()


def check_response(response):
    """Проверка api-ответа на валидность."""
    # проверка, вернулся ли в ответе dict
    if type(response) is not dict:
        raise TypeError('api-answer is not dict')

    # пытаемся получить доступ к элементам словаря
    try:
        HW_list = response['homeworks']
    except KeyError:
        logging.error('dict KeyError')
        raise KeyError('dict KeyError')
    # пытаемся получить доступ к последней домашней работе
    try:
        HW_list[0]
    except IndexError:
        logging.error('Домашняя работа не найдена')
        raise IndexError('Домашняя работа не найдена')
    # если всё успешно, возвращаем api-ответ
    else:
        return HW_list


def parse_status(homework):
    """Получаем данные о статусе домашней работы."""
    homework_name = homework['homework_name']
    homework_status = homework['status']
    verdict = HOMEWORK_STATUSES[homework_status]

    if homework_status not in HOMEWORK_STATUSES:
        raise Exception(
            f"Не могу получить статус домашней работы: '{homework_name}'."
        )
    else:
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Main bot logic."""
    logging.info("Запускаем бота")
    current_timestamp = int(time.time())

    while check_tokens() is True:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        try:
            new_HW = check_response(get_api_answer(current_timestamp))
            logging.info(
                "Функции get_api_answer и check_response сработали успешно"
            )
            message = parse_status(new_HW[0])
            logging.info("Функция parse_status сработала успешно")
            send_message(
                bot,
                message
            )

            time.sleep(RETRY_TIME)

            last_timestamp = new_HW['current_date']
            if last_timestamp:
                current_timestamp = last_timestamp

        except Exception as error:

            logging.error(f"Bot error: {error}")
            message = (f'{error}')
            send_message(bot, message)

            time.sleep(RETRY_TIME)
    else:
        logging.error("Ошибка в токенах переменной окружения")


if __name__ == '__main__':
    main()
