from django.utils import timezone
from rest_framework.exceptions import ValidationError


FORBIDDEN_NAMES = ('me')


def year_validator(year):
    if year > timezone.localtime(timezone.now()).year:
        raise ValidationError('Год выпуска произведения еще не наступил')


def forbidden_names_validator(value):
    if value.lower() in FORBIDDEN_NAMES:
        raise ValidationError(f'Нельзя использовать имя {value}')
