from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import EmailValidator
from rest_framework import serializers
from rest_framework.fields import RegexValidator

from core.consts import COUNTRY_CODES, PHONE_REGEX


class PhoneNumberField(serializers.CharField):
    default_error_messages = {
        "invalid_format": "Введите корректный номер телефона.",
        "invalid_country_code": "Данный регион не поддерживается.",
    }

    def __init__(self, **kwargs):
        kwargs["min_length"] = 15
        kwargs["max_length"] = 18
        kwargs["validators"] = [
            RegexValidator(
                regex=PHONE_REGEX, message=self.default_error_messages["invalid_format"]
            )
        ]
        super().__init__(**kwargs)


class UsernameField(serializers.CharField):
    default_error_messages = {
        "invalid": "Введите корректный телефон или email.",
        "invalid_country_code": "Данный регион не поддерживается.",
    }

    def __init__(self, **kwargs):
        kwargs.setdefault("min_length", 5)
        kwargs.setdefault("max_length", 254)
        super().__init__(**kwargs)
        self.phone_validator = RegexValidator(
            regex=PHONE_REGEX, message=self.default_error_messages["invalid"]
        )
        self.email_validator = EmailValidator(
            message=self.default_error_messages["invalid"]
        )

    def run_validation(self, data):
        value = super().run_validation(data)

        # Если это email — сразу возвращаем
        try:
            self.email_validator(value)
            return value
        except DjangoValidationError:
            pass

        # Проверяем формат телефона
        try:
            self.phone_validator(value)
        except DjangoValidationError:
            self.fail("invalid")

        # Проверяем код страны отдельно
        country_code = value.split(" ")[0]
        if country_code not in COUNTRY_CODES:
            self.fail("invalid_country_code")

        return value
