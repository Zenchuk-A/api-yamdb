from django.utils import timezone
from rest_framework.exceptions import ValidationError


def year_validator(year):
    if year > timezone.localtime(timezone.now()).year:
        raise ValidationError('Год выпуска произведения еще не наступил')
    if year < -2000:
        raise ValidationError('Нацке неизвестно о настолько древних произведениях')