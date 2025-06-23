from rest_framework.serializers import (
    ModelSerializer,
    IntegerField,
    SlugRelatedField,
    Serializer,
)
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.validators import UnicodeUsernameValidator

from reviews.models import (
    Category,
    Genre,
    Title,
    Review,
    Comment,
    USERNAME_MAX_LENGTH,
    EMAIL_MAX_LENGTH,
)
from reviews.validators import forbidden_names_validator


User = get_user_model()


class SignupSerializer(Serializer):
    username = serializers.CharField(
        required=True,
        max_length=USERNAME_MAX_LENGTH,
        validators=[UnicodeUsernameValidator(), forbidden_names_validator],
    )
    email = serializers.EmailField(
        required=True,
        max_length=EMAIL_MAX_LENGTH,
    )

    def validate(self, data):
        username = data.get('username')
        email = data.get('email')

        user_by_email = User.objects.filter(email=email).first()
        user_by_username = User.objects.filter(username=username).first()

        if user_by_email != user_by_username:
            error_msg = {}
            if user_by_email:
                error_msg['email'] = (
                    'Пользователь с таким email уже существует.'
                )
            if user_by_username:
                error_msg['username'] = (
                    'Пользователь с таким username уже существует.'
                )
            raise serializers.ValidationError(error_msg)

        return data


class TokenSerializer(Serializer):
    username = serializers.CharField(
        required=True,
        max_length=USERNAME_MAX_LENGTH,
        validators=[UnicodeUsernameValidator()],
    )
    confirmation_code = serializers.CharField(required=True)


class UserSerializer(ModelSerializer):

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'bio',
            'role',
        ]


class UserUpdateSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        read_only_fields = getattr(
            UserSerializer.Meta, 'read_only_fields', ()
        ) + ('role',)


class CategorySerializer(ModelSerializer):

    class Meta:
        model = Category
        fields = ('name', 'slug')
        lookup_field = 'slug'


class GenreSerializer(ModelSerializer):

    class Meta:
        model = Genre
        fields = ('name', 'slug')
        lookup_field = 'slug'


class TitleGetSerializer(ModelSerializer):

    category = CategorySerializer(read_only=True)
    genre = GenreSerializer(read_only=True, many=True)
    rating = IntegerField(default=None)

    class Meta:
        model = Title
        fields = (
            'id',
            'name',
            'year',
            'description',
            'genre',
            'category',
            'rating',
        )


class TitleWriteSerializer(ModelSerializer):

    category = SlugRelatedField(
        queryset=Category.objects.all(), slug_field='slug'
    )
    genre = SlugRelatedField(
        queryset=Genre.objects.all(),
        slug_field='slug',
        many=True,
        allow_empty=False,
        allow_null=False,
    )

    class Meta:
        model = Title
        fields = ('id', 'name', 'year', 'description', 'genre', 'category')

    def to_representation(self, instance):
        return TitleGetSerializer(instance).data


class ReviewSerializer(ModelSerializer):
    author = SlugRelatedField(
        read_only=True,
        slug_field='username',
    )

    class Meta:
        model = Review
        fields = ('id', 'author', 'text', 'score', 'pub_date')

    def validate(self, data):
        if self.context['request'].method == 'POST':
            title_id = self.context['view'].kwargs['title_id']
            author = self.context['request'].user
            if (
                Review.objects.all()
                .filter(author=author, title=title_id)
                .exists()
            ):
                raise serializers.ValidationError(
                    'Один автор - один отзыв на произведение'
                )
        return data


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username',
    )

    class Meta:
        model = Comment
        fields = ('id', 'author', 'text', 'pub_date')
