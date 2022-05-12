class HomeworkBotError(Exception):
    """Базовый класс для исключений."""

    pass


class GetApiAnswerError(HomeworkBotError):
    """Обработа ошибки получения статуса домашней работы."""

    pass


class ParseStatusError(HomeworkBotError):
    """Обработа ошибки получения статуса домашней работы."""

    pass
