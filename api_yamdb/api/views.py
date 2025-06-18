from rest_framework import status
from rest_framework.viewsets import GenericViewSet, ModelViewSet, ViewSet
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

from reviews.models import CustomUser, Category, Genre, Title
from .permissions import IsAdmin, ReadOnly
from .serializers import (
    SignupSerializer,
    TokenSerializer,
    UserSerializer,
    CategorySerializer,
    GenreSerializer,
    TitleGetSerializer,
    TitleWriteSerializer,
)


class SignupViewSet(ViewSet):
    permission_classes = [AllowAny]

    def create(self, request):
        serializer = SignupSerializer(data=request.data)
        email = request.data.get('email')
        username = request.data.get('username')
        if not CustomUser.objects.filter(
            username=username, email=email
        ).exists():
            if (
                CustomUser.objects.filter(username=username).exists()
                or username == 'me'
            ):
                return Response(
                    {'error': 'Пользователь с таким username уже существует.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif CustomUser.objects.filter(email=email).exists():
                return Response(
                    {'error': 'Пользователь с таким email уже существует.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                serializer.is_valid(raise_exception=True)
                user = serializer.save()
        else:
            user = CustomUser.objects.get(username=username, email=email)

        confirmation_code = default_token_generator.make_token(user)
        send_mail(
            'Confirmation Code',
            f'Your confirmation code is {confirmation_code}',
            'from@example.com',
            [user.email],
            fail_silently=False,
        )

        return Response(
            {'username': user.username, 'email': user.email},
            status=status.HTTP_200_OK,
        )


class TokenViewSet(ViewSet):
    permission_classes = [AllowAny]

    def create(self, request):
        serializer = TokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = request.data.get('username')
        confirmation_code = request.data.get('confirmation_code')

        try:
            user = CustomUser.objects.get(username=username)

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
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'Пользователь не найден'},
                status=status.HTTP_404_NOT_FOUND,
            )


class UserViewSet(ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    http_method_names = ['get', 'post', 'patch', 'delete']
    filter_backends = [SearchFilter]
    search_fields = ['username']

    def get_object(self):
        username = self.kwargs.get('username')
        try:
            if username == 'me':
                return self.request.user
            else:
                return CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            raise NotFound(detail="Пользователь не найден.")

    def partial_update(self, request, *args, **kwargs):
        user = self.get_object()

        if 'role' in request.data:
            if user == request.user or not request.user.is_admin:
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
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = (SearchFilter,)
    permission_classes = (IsAdmin | ReadOnly,)
    search_fields = ('name',)
    lookup_field = 'slug'


class GenreViewSet(CreateListDeleteViewSet):
    queryset = Genre.objects.all()
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


class TitleViewSet(ModelViewSet):
    queryset = Title.objects.all()
    permission_classes = (IsAdmin | ReadOnly,)
    http_method_names = ('get', 'head', 'options', 'post', 'delete', 'patch')
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filterset_class = TitleFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return TitleGetSerializer
        return TitleWriteSerializer
