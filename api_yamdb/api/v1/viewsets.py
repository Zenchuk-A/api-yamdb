from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    DestroyModelMixin,
)


class CreateListDeleteViewSet(
    GenericViewSet, CreateModelMixin, ListModelMixin, DestroyModelMixin
):
    pass
