from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


from .views import (
    SignupViewSet,
    TokenViewSet,
    UserViewSet,
)

router_v1 = routers.DefaultRouter()
router_v1.register('signup', SignupViewSet, basename='signup')
router_v1.register('token', TokenViewSet, basename='token')
router_v1.register('users', UserViewSet, basename='users')


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
