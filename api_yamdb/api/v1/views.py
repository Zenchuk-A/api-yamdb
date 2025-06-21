from rest_framework.decorators import api_view, permission_classes, action
from rest_framework import status
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.mixins import CreateModelMixin
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.db.models import Avg

from reviews.models import UserProfile, Category, Genre, Title, Review
from .permissions import (
    IsAdmin,
    ReadOnly,
    IsAuthorOrModeratorOrReadOnly,
    IsAdminOrReadOnlyRole,
)
from .serializers import (
    SignupSerializer,
    TokenSerializer,
    UserSerializer,
    CategorySerializer,
    GenreSerializer,
    TitleGetSerializer,
    TitleWriteSerializer,
    ReviewSerializer,
    CommentSerializer,
)
from .viewsets import CreateListDeleteViewSet
from .filters import TitleFilter


@api_view(['POST'])
@permission_classes([AllowAny])
def signup_view(request):
    serializer = SignupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data['email']
    username = serializer.validated_data['username']

    user, created = UserProfile.objects.get_or_create(
        username=username, defaults={'email': email}
    )

    if not created and user.email != email:
        return Response(
            {'error': 'Пользователь с таким username уже существует.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    confirmation_code = default_token_generator.make_token(user)
    send_mail(
        'Confirmation Code',
        f'Your confirmation code is {confirmation_code}',
        settings.EMAIL,
        [user.email],
        fail_silently=False,
    )

    return Response(
        {'username': user.username, 'email': user.email},
        status=status.HTTP_200_OK,
    )


class TokenViewSet(CreateModelMixin, GenericViewSet):
    serializer_class = TokenSerializer
    permission_classes = [AllowAny]

    def create(self, request):
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']
        confirmation_code = serializer.validated_data['confirmation_code']

        user = get_object_or_404(UserProfile, username=username)

        if not default_token_generator.check_token(user, confirmation_code):
            raise ValidationError(
                {'confirmation_code': 'Неверный код подтверждения'}
            )

        token = AccessToken.for_user(user)
        return Response({'token': str(token)}, status=status.HTTP_200_OK)


class UserViewSet(ModelViewSet):
    queryset = UserProfile.objects.all().order_by('username')
    serializer_class = UserSerializer
    permission_classes = [IsAdmin, IsAdminOrReadOnlyRole]
    lookup_field = 'username'
    http_method_names = ['get', 'post', 'patch', 'delete']
    filter_backends = [SearchFilter]
    search_fields = ['username']

    @action(
        detail=False,
        methods=['get', 'patch'],
        permission_classes=[IsAuthenticated],
        url_path='me',
    )
    def me(self, request):
        user = request.user

        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return Response(serializer.data)

        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class CategoryViewSet(CreateListDeleteViewSet):
    queryset = Category.objects.all().order_by('id')
    serializer_class = CategorySerializer
    filter_backends = (SearchFilter,)
    permission_classes = (IsAdmin | ReadOnly,)
    search_fields = ('name',)
    lookup_field = 'slug'


class GenreViewSet(CreateListDeleteViewSet):
    queryset = Genre.objects.all().order_by('id')
    serializer_class = GenreSerializer
    filter_backends = (SearchFilter,)
    permission_classes = (IsAdmin | ReadOnly,)
    search_fields = ('name',)
    lookup_field = 'slug'


class WithoutPutViewSet(ModelViewSet):
    http_method_names = ('get', 'head', 'options', 'post', 'delete', 'patch')


class TitleViewSet(WithoutPutViewSet):    
    queryset = Title.objects.annotate(rating=Avg('reviews__score'))
    permission_classes = (IsAdmin | ReadOnly,)
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filterset_class = TitleFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return TitleGetSerializer
        return TitleWriteSerializer


class ReviewViewSet(WithoutPutViewSet):
    serializer_class = ReviewSerializer
    permission_classes = (IsAuthorOrModeratorOrReadOnly,)

    def get_queryset(self):
        title = get_object_or_404(Title, id=self.kwargs['title_id'])
        return title.reviews.all().order_by('id')
    
    def perform_create(self, serializer):
        title_id = self.kwargs['title_id']        
        title = get_object_or_404(Title, pk=title_id)        
        serializer.save(author=self.request.user, title=title)        


class CommentViewSet(WithoutPutViewSet):
    serializer_class = CommentSerializer
    permission_classes = (IsAuthorOrModeratorOrReadOnly,)

    def get_queryset(self):
        review = get_object_or_404(
            Review, id=self.kwargs['review_id'], title=self.kwargs['title_id'])
        return review.comments.all().order_by('id')

    def perform_create(self, serializer):
        review_id = self.kwargs['review_id']
        review = get_object_or_404(Review, pk=review_id)
        serializer.save(author=self.request.user, review=review)
