from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

from .validators import year_validator


class UserRole(models.TextChoices):
    USER = ('user', 'Аутентифицированный пользователь')
    MODERATOR = ('moderator', 'Модератор')
    ADMIN = ('admin', 'Администратор')


class CustomUser(AbstractUser):
    bio = models.TextField('Биография', blank=True)
    role = models.CharField(
        'Роль',
        max_length=10,
        choices=UserRole.choices,
        default=UserRole.USER
    )

    @property
    def is_authenticated(self):
        return self.role in [UserRole.USER, UserRole.MODERATOR, UserRole.ADMIN]

    @property
    def is_moderator(self):
        return self.role == UserRole.MODERATOR or self.is_superuser

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN or self.is_superuser

class Categories(models.Model):
    """Класс для описания категорий произведений."""

    name = models.CharField('Категория', max_length=256)
    slug = models.SlugField('Слаг категории', max_length=50, unique=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Genres(models.Model):
    """Класс для описания жанров произведений."""

    name = models.CharField('Жанр', max_length=256)
    slug = models.SlugField('Слаг жанра', max_length=50, unique=True)

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'

    def __str__(self):
        return self.name


class Titles(models.Model):
    """Класс для описания произведения."""

    name = models.CharField('Название', max_length=256)
    year = models.IntegerField(
        'Год выпуска',
        validators=[year_validator]
    )
    description = models.TextField('Описание', null=True, blank=True)
    genre = models.ManyToManyField('Genres', related_name='titles')
    category = models.ForeignKey('Categories', related_name='titles',
                                 on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = 'Фильм'
        verbose_name_plural = 'Фильмы'
        ordering = ('name',)

    def __str__(self):
        return self.name


class BaseCommentsAndReviews(models.Model):
    """Базовый класс для отзывов и комментариев."""

    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    text = models.TextField('Текст')

    class Meta:
        abstract = True
        ordering = ('pub_date',)


class Reviews(BaseCommentsAndReviews):
    """Класс для отзывов на произведения."""

    author = models.ForeignKey('reviews.CustomUser', related_name='reviews',
                               on_delete=models.CASCADE)
    title = models.ForeignKey('Titles', related_name='reviews',
                              on_delete=models.CASCADE)
    score = models.IntegerField(
        'Оценка',
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'

    def __str__(self):
        return self.text


class Comments(BaseCommentsAndReviews):
    """Класс комментариев к отзывам."""

    author = models.ForeignKey('reviews.CustomUser', related_name='comments',
                               on_delete=models.CASCADE)
    review = models.ForeignKey('Reviews', related_name='comments',
                               on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return self.text
