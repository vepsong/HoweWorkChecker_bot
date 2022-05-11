class Error(Exception):
    """Базовый класс для исключений."""

    pass


class GetApiAnswerError(Error):
    """Обработа ошибки получения статуса домашней работы."""

    pass


class ParseStatusError(Error):
    """Обработа ошибки получения статуса домашней работы."""

    pass
