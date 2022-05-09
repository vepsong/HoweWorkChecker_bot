class error(Exception):
    """Базовый класс для остальных исключений."""

    pass


class send_message_error(error):
    """Обработа ошибок отправки сообщения пользователю."""

    pass


class get_api_answer_error(error):
    """Обработка ошибок получения api-ответа."""

    pass


class homework_error(error):
    """Обработка програмных исключений."""

    pass
