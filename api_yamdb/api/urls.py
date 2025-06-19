from django.urls import path, include
from rest_framework.routers import DefaultRouter


from .views import (
    SignupViewSet,
    TokenViewSet,
    UserViewSet,
    CategoryViewSet,
    GenreViewSet,
    TitleViewSet,
    ReviewViewSet,
    CommentViewSet,
)


router_v1 = DefaultRouter()
router_v1.register('signup', SignupViewSet, basename='signup')
router_v1.register('token', TokenViewSet, basename='token')
router_v1.register('users', UserViewSet, basename='users')
router_v1.register('categories', CategoryViewSet, 'categories')
router_v1.register('genres', GenreViewSet, 'genres')
router_v1.register(
    r'titles/(?P<title_id>\d+)/reviews', ReviewViewSet, 'reviews'
)
router_v1.register(
    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
    CommentViewSet,
    'comments',
)
router_v1.register('titles', TitleViewSet, 'titles')


urlpatterns = [
    path('v1/auth/', include(router_v1.urls)),
    path(
        'v1/users/<str:username>/',
        UserViewSet.as_view(
            {'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}
        ),
        name='user-detail',
    ),
    path('v1/', include(router_v1.urls)),
]
