import re

from rest_framework import serializers

# +7 777 123 4567
PHONE_REGEX = r"^\+7\s\d{3}\s\d{3}\s\d{4}$"


class PhoneNumberField(serializers.CharField):
    default_error_messages = {
        "invalid_format": "Неверный формат.",
    }

    def __init__(self, **kwargs):
        # Устанавливаем фиксированные значения min_length и max_length
        kwargs["min_length"] = 15
        kwargs["max_length"] = 17
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        # Проверка формата номера
        if not re.match(PHONE_REGEX, value):
            self.fail("invalid_format")

        return value
