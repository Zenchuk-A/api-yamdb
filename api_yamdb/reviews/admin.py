from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from reviews.models import UserProfile


UserAdmin.fieldsets += (
    (
        'Extra Fields',
        {
            'fields': (
                'bio',
                'role',
            )
        },
    ),
)

admin.site.register(UserProfile, UserAdmin)
