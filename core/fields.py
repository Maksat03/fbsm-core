import re

from rest_framework import serializers
from rest_framework.fields import RegexValidator

from core.consts import COUNTRY_CODES

codes_pattern = "|".join(re.escape(code) for code in COUNTRY_CODES)

PHONE_REGEX = rf"^({codes_pattern})\s\d{{3}}\s\d{{3}}\s\d{{4}}$"

pattern = re.compile(PHONE_REGEX)


class PhoneNumberField(serializers.CharField):
    default_error_messages = {
        "invalid_format": "Неверный формат.",
    }

    def __init__(self, **kwargs):
        kwargs["min_length"] = 15
        kwargs["max_length"] = 17
        kwargs["validators"] = [
            RegexValidator(
                regex=PHONE_REGEX, message=self.default_error_messages["invalid_format"]
            )
        ]
        super().__init__(**kwargs)
