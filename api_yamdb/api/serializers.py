from django.core.validators import RegexValidator
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework import serializers
from django.db.models import Sum

from reviews.models import CustomUser, Category, Genre, Title, Review, Comment

username_validator = RegexValidator(
    regex=r'^[\w.@+-]+\Z',
    message='Username must be alphanumeric and '
    'can contain @ . + - _ characters.',
)


class SignupSerializer(ModelSerializer):
    username = serializers.CharField(
        required=True, max_length=150, validators=[username_validator]
    )
    email = serializers.EmailField(required=True, max_length=254)

    class Meta:
        model = CustomUser
        fields = ['username', 'email']


class TokenSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, max_length=150)
    confirmation_code = serializers.CharField(required=True)


class UserSerializer(SignupSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'bio',
            'role',
        ]

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Пользователь с таким email уже существует."
            )
        return value

    def validate_username(self, value):
        if value == 'me' or CustomUser.objects.filter(username=value):
            raise serializers.ValidationError(
                "Пользователь с таким username уже существует."
            )
        return value


class CategorySerializer(ModelSerializer):

    class Meta:
        model = Category
        fields = ('name', 'slug')


class GenreSerializer(ModelSerializer):

    class Meta:
        model = Genre
        fields = ('name', 'slug')


class TitleSerializer(ModelSerializer):

    rating = SerializerMethodField()

    class Meta:
        model = Title
        fields = ('id', 'name', 'year', 'description', 'genre', 'category', 'rating')

    def get_rating(self, obj):
        reviews = obj.reviews
        result = reviews.aggregate(sum_of_ratings=Sum('rating'))
        return round(result['sum_of_ratings'] / reviews.count()) 
        
