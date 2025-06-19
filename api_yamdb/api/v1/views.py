from rest_framework import status
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.exceptions import NotFound
from rest_framework.filters import SearchFilter
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    DestroyModelMixin,
)
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
from django.shortcuts import get_object_or_404
from django.conf import settings

from reviews.models import UserProfile, Category, Genre, Title, Review
from .permissions import IsAdmin, ReadOnly, IsAuthorOrModeratorOrReadOnly
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


class SignupViewSet(CreateModelMixin, GenericViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = SignupSerializer
    permission_classes = [AllowAny]

    def create(self, request):
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        username = serializer.validated_data['username']
        user = UserProfile.objects.filter(
            username=username, email=email
        ).first()

        if not user:
            if (
                UserProfile.objects.filter(username=username).exists()
                or username == 'me'
            ):
                return Response(
                    {'error': 'Пользователь с таким username уже существует.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif UserProfile.objects.filter(email=email).exists():
                return Response(
                    {'error': 'Пользователь с таким email уже существует.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                user = serializer.save()

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

        try:
            user = UserProfile.objects.get(username=username)

            if default_token_generator.check_token(user, confirmation_code):
                token = AccessToken.for_user(user)
                return Response(
                    {'token': str(token)}, status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': 'Неверный код подтверждения'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'Пользователь не найден'},
                status=status.HTTP_404_NOT_FOUND,
            )


class UserViewSet(ModelViewSet):
    queryset = UserProfile.objects.all().order_by('username')
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    http_method_names = ['get', 'post', 'patch', 'delete']
    filter_backends = [SearchFilter]
    search_fields = ['username']

    def get_object(self):
        username = self.kwargs.get('username')
        if username == 'me':
            return self.request.user
        try:
            return UserProfile.objects.get(username=username)
        except UserProfile.DoesNotExist:
            raise NotFound(detail="Пользователь не найден.")

    def partial_update(self, request, *args, **kwargs):
        user = self.get_object()

        if 'role' in request.data and (
            user == request.user or not request.user.is_admin
        ):
            return Response(
                {"detail": "Изменение роли запрещено."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().partial_update(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        if self.kwargs.get('username') == 'me':
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
        user = self.get_object()
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CreateListDeleteViewSet(
    GenericViewSet, CreateModelMixin, ListModelMixin, DestroyModelMixin
):
    pass


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


class TitleFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(
        field_name='category__slug',
    )
    genre = django_filters.CharFilter(
        field_name='genre__slug',
    )
    name = django_filters.CharFilter(
        field_name='name',
    )
    year = django_filters.NumberFilter(
        field_name='year',
    )


class WithoutPutViewSet(ModelViewSet):
    http_method_names = ('get', 'head', 'options', 'post', 'delete', 'patch')


class TitleViewSet(WithoutPutViewSet):
    queryset = Title.objects.all()
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


class CommentViewSet(WithoutPutViewSet):
    serializer_class = CommentSerializer
    permission_classes = (IsAuthorOrModeratorOrReadOnly,)

    def get_queryset(self):
        review = get_object_or_404(Review, id=self.kwargs['review_id'])
        return review.comments.all().order_by('id')
