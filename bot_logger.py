import logging
from logging.handlers import RotatingFileHandler


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


# проверка использования логгера
def check_logger():
    """Запуск логгера с тестовыми данными для проверки."""
    logger.debug('debug message')
    logger.info('info message')
    logger.warning('warn message')
    logger.error('error message')
    logger.critical('critical message')


if __name__ == '__main__':
    check_logger()
