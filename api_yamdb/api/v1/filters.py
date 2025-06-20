import django_filters


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
