from rest_framework.serializers import ModelSerializer, SerializerMethodField
from django.db.models import Sum

from reviews.models import CustomUser, Category, Genre, Title, Review, Comment


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
        
