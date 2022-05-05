import logging
import os
import time

from dotenv import load_dotenv
import requests
import telegram
from telegram import Bot


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
    list = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    if all(list):
        return True

    for i in list:
        if i is None:
            return False


RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

bot = Bot(token=TELEGRAM_TOKEN)

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Func for sending messages."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info('Message sent')
    except Exception as error:
        logging.error(f"Message wasn't sent {error}")


def get_api_answer(current_timestamp):
    """Receiving data from Yandex."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    # params = {'from_date': 0}

    try:
        response = requests.get(
            ENDPOINT,
            params=params,
            headers=HEADERS,
        )
        logging.info('we got api-answer')
        print(response.json())
        # check_response(response)
        return response.json()
    except Exception:
        logging.error(f"{Exception} can't get api-answer")


def check_response(response):
    """Checking api-answer."""
    if type(response) is not dict:
        raise TypeError('api-answer is not dict')
    try:
        HW_list = response['homeworks']
    except KeyError:
        logging.error('dict KeyError')
        raise KeyError('dict KeyError')
    try:
        HW = HW_list[0]
    except IndexError:
        logging.error('Homework not found')
        raise IndexError('Homework not found')
    return HW


def parse_status(homework):
    """Receiving data about homework status."""

    try:
        homework_name = homework.get('homework_name')
    except Exception as error:
        logging.error("Can't get HW name.")
        raise error("Can't get HW name.")

    try:
        homework_status = homework.get('status')
        verdict = HOMEWORK_STATUSES[homework_status]
        return f'"{homework_name}" status was changed to: {verdict}'
    except Exception as error:
        logging.error(f"Can't get HW status '{homework_name}'.")
        raise error(f"Can't get HW status '{homework_name}'.")


def main():
    """Main bot logic."""
    logging.debug("Start bot")
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while check_tokens() is True:
        try:
            new_HW = get_api_answer(current_timestamp)

            if new_HW.get('homeworks'):
                message = parse_status(new_HW.get('homeworks')[0])
                send_message(
                    bot,
                    message
                )
            else:
                message = 'You have no active homeworks'
                send_message(
                    bot,
                    message
                )
            logging.debug("Got data")

            time.sleep(RETRY_TIME)

            last_timestamp = new_HW['current_date']
            if last_timestamp:
                current_timestamp = last_timestamp

        except Exception as error:

            logging.debug(f"Bot error: {error}")

            message = f'Program error: {error}'

            send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
