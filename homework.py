import logging
from logging.handlers import RotatingFileHandler
import os
import sys
import time

from exceptions import get_api_answer_error
from dotenv import load_dotenv
import requests
import telegram


# создание логгера
logger = logging.getLogger(__name__)
# установка уровня логирования
logger.setLevel(logging.DEBUG)

# создание обработчика с логированием в файл
file_handler = RotatingFileHandler(
    "homework_bot.log",
    mode="w",
    maxBytes=(1024 * 100),
    backupCount=1
)

# установка уровня логирования обработчика
file_handler.setLevel(logging.DEBUG)

# создание шаблона отображения
formatter = logging.Formatter(
    '%(asctime)s, %(levelname)s, %(funcName)s, '
    '%(lineno)s, %(message)s, %(name)s'
)

# связвание обработчиков с шаблоном форматирования
file_handler.setFormatter(formatter)

# добавление обработчика логгеру
logger.addHandler(file_handler)


# загружаю переменные среды окружения
load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


def check_tokens():
    """Сhecking env variables."""
    env_vars = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }

    # создаю список с None - значениями env vars
    none_env_vars_list = [
        name for name, value in env_vars.items() if value is None
    ]

    # если список пустой, значит отсутствуют None - значения env vars
    if not none_env_vars_list:
        logger.debug("Все env-переменные на месте")
        return True
    elif none_env_vars_list:
        logger.critical(f"Отсутствует env-переменная {none_env_vars_list}")
        return False


RETRY_TIME = (5)
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statusesZ/'
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
        logger.info('Отправили сообщение')
    except telegram.error.BadRequest as error:
        logger.error(
            (f"Не смогли отправить сообщение: {error}"),
            exc_info=True
        )


def get_api_answer(current_timestamp):
    """Получаем api-ответ от сервера Yandex."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    try:
        logger.debug(
            f'Отправляем api-запрос: '
            f'ENDPOINT = {ENDPOINT}, '
            f'params = {params}, '
            f'HEADERS = {HEADERS}'
        )

        response = requests.get(
            ENDPOINT,
            params=params,
            headers=HEADERS,
        )
    except requests.exceptions.RequestException as error:
        logger.error(
            (f'{error}: не получили api-ответ'),
            exc_info=True
        )

        raise error

    mistake_message = (f'Проблемы соединения с сервером.'
                       f' Ошибка {response.status_code}')

    if response.status_code == requests.codes.ok:
        return response.json()
    elif response.status_code != requests.codes.ok:
        logger.error(
            mistake_message,
            exc_info=True
        )
        raise get_api_answer_error(mistake_message)


def check_response(response):
    """Проверка api-ответа на валидность."""
    # проверка, вернулся ли в ответе dict
    if not isinstance(response, dict):
        raise TypeError('api-ответ is not dict')

    # пытаемся получить доступ к элементам словаря
    try:
        HW_list = response['homeworks']
    except KeyError:
        logger.error('dict KeyError')
        raise KeyError('dict KeyError')
    # пытаемся получить доступ к последней домашней работе
    try:
        HW_list[0]
    except IndexError:
        logger.warning('Домашняя работа не найдена')
        raise IndexError('Домашняя работа не найдена')
    # если всё успешно, возвращаем api-ответ
    else:
        return HW_list


def parse_status(homework):
    """Получаем данные о статусе домашней работы."""
    homework_name = homework['homework_name']
    homework_status = homework['status']
    verdict = HOMEWORK_STATUSES[homework_status]

    if homework_status in HOMEWORK_STATUSES:
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    else:
        logger.error(Exception)
        raise Exception(
            f"Не могу получить статус домашней работы: '{homework_name}'."
        )


class run_count:
    """Подсчёт кол-ва запусков программы."""

    stop = 3
    counter = 0

    def __init__(self):
        run_count.counter += 1
        print(run_count.counter)

        if run_count.stop == run_count.counter:
            logger.error("Программа окончательно остановлена")
            run_count.counter = 0
            raise sys.exit(1)
        else:
            logger.debug(
                f"Попытка перезапустить программу N: {run_count.counter} "
                f"из {run_count.stop}"
            )
            time.sleep(RETRY_TIME)
            main()


class compare_messages:
    """Сравниваем сообщения."""

    old_message = None

    def __init__(self, message):
        """Инициализация переменных."""
        self.message = message

    def comparing(self):
        """Сравниваем старое и новое сообщения между собой."""
        logger.debug(f'Предыдущее сообщение {compare_messages.old_message}')
        logger.debug(f'Текущее сообщение {self.message}')

        if compare_messages.old_message != self.message:
            logger.info('Старое сообщение отличается от текущего сообщения')
            compare_messages.old_message = self.message
            return True
        elif compare_messages.old_message == self.message:
            logger.info('Старое сообщение не отличается от текущего сообщения')
            return False


def main():
    """Основная логика работы бота."""
    logger.info("Запускаем бота")
    current_timestamp = int(time.time())
    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    if check_tokens() is False:
        logger.info("Программа временно остановлена")
        logger.debug(
            f"Ждём {RETRY_TIME} сек и пробуем запустить программу заново"
        )
        # фиксируем факт неудачного запуска программы
        run_count()

    while True:

        try:
            new_HW = check_response(get_api_answer(current_timestamp))
            logger.info(
                "Функции get_api_answer и check_response сработали успешно"
            )
            message = parse_status(new_HW[0])
            logger.info("Функция parse_status сработала успешно")

        except get_api_answer_error as error:
            message = (f'{error}')

        except Exception as error:
            message = (f'{error}')

        finally:
            # сравниваем полученные сообщения между собой
            # если сообщение содержит новую инфо — отправляем его пользователю
            # если нет — логгируем
            if compare_messages(message).comparing() is True:
                send_message(bot, message)

            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
