from django.core.validators import RegexValidator
from rest_framework.serializers import ModelSerializer, SerializerMethodField, SlugRelatedField
from rest_framework import serializers
from django.db.models import Avg
from django.shortcuts import get_object_or_404

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
        lookup_field = 'slug'


class GenreSerializer(ModelSerializer):

    class Meta:
        model = Genre
        fields = ('name', 'slug')
        lookup_field = 'slug'


class TitleGetSerializer(ModelSerializer):

    category = CategorySerializer(read_only=True)
    genre = GenreSerializer(read_only=True, many=True)
    # rating = SerializerMethodField()

    class Meta:
        model = Title
        fields = ('id', 'name', 'year', 'description', 'genre', 'category', 'rating')

    # def get_rating(self, obj):
        # reviews = obj.reviews
        # result = reviews.aggregate(avg=Avg('rating'))
        # return round(result['avg'])


class TitleWriteSerializer(ModelSerializer):

    category = SlugRelatedField(
        queryset=Category.objects.all(),
        slug_field='slug'
    )
    genre = SlugRelatedField(
        queryset=Genre.objects.all(),
        slug_field='slug',
        many=True
    )

    class Meta:
        model = Title
        fields = ('id', 'name', 'year', 'description', 'genre', 'category')


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
            title = get_object_or_404(Title, pk=title_id)
            author = self.context['request'].user
            if title.reviews.filter(author=author).exists():
                raise serializers.ValidationError(
                    'Один автор - один отзыв на произведение')
            data['author'] = author
            data['title'] = title
        return data


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username',
    )

    class Meta:
        model = Comment
        fields = ('id', 'author', 'text', 'pub_date')
        read_only_fields = ('review',)

    def create(self, data):
        review_id = self.context['view'].kwargs['review_id']
        review = get_object_or_404(Review, pk=review_id)
        data['author'] = self.context['request'].user
        data['review'] = review
        return super().create(data)
