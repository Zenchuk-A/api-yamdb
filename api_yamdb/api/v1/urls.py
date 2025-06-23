from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    signup_view,
    TokenViewSet,
    UserViewSet,
    CategoryViewSet,
    GenreViewSet,
    TitleViewSet,
    ReviewViewSet,
    CommentViewSet,
)


router_v1_auth = DefaultRouter()
router_v1_auth.register('token', TokenViewSet, basename='token')
router_v1 = DefaultRouter()
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
    path('auth/signup/', signup_view, name='signup'),
    path('auth/', include(router_v1_auth.urls)),
    path('', include(router_v1.urls)),
]
