from bot_logger import logger
import os
import sys
import time

from dotenv import load_dotenv
# from exceptions import send_message_error, get_api_answer_error
import requests
import telegram


# logging.basicConfig(
#     level=logging.DEBUG,
#     filename='homework_bot.log',
#     filemode='w',
#     format=(
#         '%(asctime)s, %(levelname)s, %(funcName)s, '
#         '%(lineno)s, %(message)s, %(name)s'
#     )
# )

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
        logger.debug("Все переменные окружения на месте")
        return True
    elif none_env_vars_list:
        logger.error(f"Отсутствует переменная окружения {none_env_vars_list}")
        return False


RETRY_TIME = (5)
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
        logger.info('Отправили сообщение')
    except telegram.TelegramError as error:
        logger.error(
            (f"Не смогли отправить сообщение: {error}"),
            exc_info=True
        )
        raise error


def get_api_answer(current_timestamp):
    """Получаем api-ответ от сервера Yandex."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    # params = {'from_date': 0}

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
        logger.error(mistake_message)
        raise TypeError(mistake_message)


def check_response(response):
    """Проверка api-ответа на валидность."""
    # проверка, вернулся ли в ответе dict
    if not isinstance(response, dict):
        raise TypeError(f'api-ответ is not dict {response}')

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
        logger.error('Домашняя работа не найдена')
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


def try_start_counter():
    """Подсчёт кол-ва запусков программы."""
    try_start_counter.counter += 1


try_start_counter.counter = 0


def main():
    """Основная логика работы бота."""
    logger.info("Запускаем бота")
    current_timestamp = int(time.time())
    old_message = None
    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    if check_tokens() is False:
        logger.info("Программа временно остановлена")
        logger.debug(
            f"Ждём {RETRY_TIME} сек и пробуем запустить программу заново"
        )
        try_start_counter()
        logger.debug(
            f"Попытка перезапустить программу N: {try_start_counter.counter}"
        )
        if try_start_counter.counter != 3:
            time.sleep(RETRY_TIME)
            main()
        else:
            logger.warning("Программа окончательно остановлена")
            raise sys.exit(1)

    while True:

        try:
            new_HW = check_response(get_api_answer(current_timestamp))
            logger.info(
                "Функции get_api_answer и check_response сработали успешно"
            )
            message = parse_status(new_HW[0])
            logger.info("Функция parse_status сработала успешно")

        except Exception as error:
            message = (f'{error}')

        finally:

            # пользователь получает только уникальные сообщения
            logger.debug('Проверка идентичности cообщений бота')
            if old_message != message:
                logger.debug('Пред. сообщение бота отличается от текущего')
                logger.info('Отправляем пользователю сообщение')
                try:
                    send_message(bot, message)
                    old_message = message
                except Exception as error:
                    logger.error(error)

            else:
                logger.debug('Пред. сообщение бота идентично текущему')
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
