from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

from .validators import year_validator, MeNameValidator


USER_ROLE_MAX_LENGTH = 10
CATEGORY_MAX_LENGTH = 256
CATEGORY_SLUG_MAX_LENGTH = 50
GENRE_MAX_LENGTH = 256
GENRE_SLUG_MAX_LENGTH = 50
TITLE_MAX_LENGTH = 256
SCORE_MIN_VALUE = 1
SCORE_MAX_VALUE = 10
USERNAME_MAX_LENGTH = 150
EMAIL_MAX_LENGTH = 254


class UserRole(models.TextChoices):
    USER = ('user', 'Аутентифицированный пользователь')
    MODERATOR = ('moderator', 'Модератор')
    ADMIN = ('admin', 'Администратор')


class UserProfile(AbstractUser):
    """Класс пользователей."""

    email = models.EmailField(
        'Адрес электронной почты', unique=True, max_length=EMAIL_MAX_LENGTH
    )
    username = models.CharField(
        'Логин',
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        validators=[UnicodeUsernameValidator, MeNameValidator],
    )
    bio = models.TextField('Биография', blank=True)
    role = models.CharField(
        'Роль',
        max_length=USER_ROLE_MAX_LENGTH,
        choices=UserRole.choices,
        default=UserRole.USER,
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username

    @property
    def is_moderator(self):
        return self.role == UserRole.MODERATOR

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN or self.is_superuser


class Category(models.Model):
    """Класс для описания категорий произведений."""

    name = models.CharField('Категория', max_length=CATEGORY_MAX_LENGTH)
    slug = models.SlugField(
        'Слаг категории', max_length=CATEGORY_SLUG_MAX_LENGTH, unique=True
    )

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ('name',)

    def __str__(self):
        return f'Категория произведения: {self.name}'


class Genre(models.Model):
    """Класс для описания жанров произведений."""

    name = models.CharField('Жанр', max_length=GENRE_MAX_LENGTH)
    slug = models.SlugField(
        'Слаг жанра', max_length=GENRE_SLUG_MAX_LENGTH, unique=True
    )

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'
        ordering = ('name',)

    def __str__(self):
        return f'Жанр произведения: {self.name}'


class Title(models.Model):
    """Класс для описания произведения."""

    name = models.CharField('Название', max_length=TITLE_MAX_LENGTH)
    year = models.SmallIntegerField('Год выпуска', validators=[year_validator])
    description = models.TextField('Описание', null=True, blank=True)
    genre = models.ManyToManyField('Genre', related_name='titles')
    category = models.ForeignKey(
        'Category', related_name='titles', on_delete=models.SET_NULL, null=True
    )
    # rating = models.IntegerField('Рейтинг', null=True, blank=True)

    class Meta:
        verbose_name = 'Фильм'
        verbose_name_plural = 'Фильмы'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Review(models.Model):
    """Класс для отзывов на произведения."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='reviews',
        on_delete=models.CASCADE,
    )
    title = models.ForeignKey(
        'Title', related_name='reviews', on_delete=models.CASCADE
    )
    score = models.IntegerField(
        'Оценка',
        validators=[
            MinValueValidator(SCORE_MIN_VALUE),
            MaxValueValidator(SCORE_MAX_VALUE),
        ],
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    text = models.TextField('Текст')

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'title'], name='unique_review_author_title'
            )
        ]
        ordering = ('pub_date',)

    def __str__(self):
        return f'Отзыв на произведение: {self.name}'


class Comment(models.Model):
    """Класс комментариев к отзывам."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='comments',
        on_delete=models.CASCADE,
    )
    review = models.ForeignKey(
        'Review', related_name='comments', on_delete=models.CASCADE
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    text = models.TextField('Текст')

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ('pub_date',)

    def __str__(self):
        return f'Комментарий к отзыву: {self.name}'
