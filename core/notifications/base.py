from abc import ABC
from enum import Enum


class NotificationLevel(Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    DANGER = "danger"


class Notification(ABC):
    """
    Базовый класс для отправки уведомлений пользователям

    type: тип уведомления
    level: уровень уведомления (как в logging)

    Для создания нового типа уведомления нужно унаследоваться от этого класса,
    применить dataclass и определить type и level, а также остальные метаданные
    """

    type: str
    level: NotificationLevel
