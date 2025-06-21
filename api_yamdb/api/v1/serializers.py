from django.core.validators import RegexValidator, EmailValidator
from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
    SlugRelatedField,
    Serializer,
)
from rest_framework import serializers
from django.contrib.auth import get_user_model

from reviews.models import (
    UserProfile,
    Category,
    Genre,
    Title,
    Review,
    Comment,
    USERNAME_MAX_LENGTH,
    EMAIL_MAX_LENGTH,
)
from reviews.validators import menamevalidator


User = get_user_model()

username_validator = RegexValidator(
    regex=r'^[\w.@+-]+\Z',
    message='Username must be alphanumeric and '
    'can contain @ . + - _ characters.',
)


class SignupSerializer(Serializer):
    username = serializers.CharField(
        required=True,
        max_length=USERNAME_MAX_LENGTH,
        validators=[username_validator, menamevalidator],
    )
    email = serializers.EmailField(
        required=True,
        max_length=EMAIL_MAX_LENGTH,
        validators=[EmailValidator],
    )

    def validate(self, data):
        username = data.get('username')
        email = data.get('email')

        user_by_email = User.objects.filter(email=email).first()
        user_by_username = User.objects.filter(username=username).first()

        if (
            user_by_email
            and user_by_username
            and user_by_email != user_by_username
        ):
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

        if user_by_username and (
            not user_by_email or user_by_email == user_by_username
        ):
            if user_by_username.email != email:
                raise serializers.ValidationError(
                    {
                        'username':
                        'Username уже используется другим пользователем.'
                    }
                )

        if user_by_email and (
            not user_by_username or user_by_username == user_by_email
        ):
            if user_by_email.username != username:
                raise serializers.ValidationError(
                    {'email': 'Email уже используется другим пользователем.'}
                )

        return data


class TokenSerializer(Serializer):
    username = serializers.CharField(
        required=True,
        max_length=USERNAME_MAX_LENGTH,
        validators=[username_validator],
    )
    confirmation_code = serializers.CharField(required=True)


class UserSerializer(ModelSerializer):

    username = serializers.CharField(
        required=True,
        max_length=USERNAME_MAX_LENGTH,
        validators=[username_validator, menamevalidator],
    )

    class Meta:
        model = UserProfile
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'bio',
            'role',
        ]

    def validate_email(self, value):
        user = self.instance
        if (
            UserProfile.objects.filter(email=value)
            .exclude(pk=user.pk if user else None)
            .exists()
        ):
            raise serializers.ValidationError(
                "Пользователь с таким email уже существует."
            )
        return value

    def validate_username(self, value):
        user = self.instance
        if (
            value == 'me'
            or UserProfile.objects.filter(username=value)
            .exclude(pk=user.pk if user else None)
            .exists()
        ):
            raise serializers.ValidationError(
                "Пользователь с таким username уже существует."
            )
        return value

    def update(self, instance, validated_data):
        request = self.context.get('request')
        if request and not (
            request.user.is_authenticated and request.user.is_admin
        ):
            validated_data.pop('role', None)
        return super().update(instance, validated_data)


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
    rating = SerializerMethodField()

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

    def get_rating(self, obj):
        return round(obj.rating) if obj.rating else None


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
        representation = super().to_representation(instance)
        representation['rating'] = 0
        representation['category'] = CategorySerializer(instance.category).data
        representation['genre'] = GenreSerializer(
            instance.genre, many=True
        ).data
        return representation


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
