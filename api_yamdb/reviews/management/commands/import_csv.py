import csv
import os
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime

from reviews.models import (
    UserProfile,
    Category,
    Genre,
    Title,
    Review,
    Comment,
)


class Command(BaseCommand):
    help = 'Import data from CSV files to DB'

    def handle(self, *args, **kwargs):
        self.import_users()
        self.import_categories()
        self.import_genres()
        self.import_titles()
        self.import_genre_title()
        self.import_reviews()
        self.import_comments()
        self.stdout.write(self.style.SUCCESS('Data imported successfully'))

    def import_users(self):
        file_path = os.path.join(
            settings.BASE_DIR, 'static', 'data', 'users.csv'
        )
        with open(file_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                UserProfile.objects.update_or_create(
                    id=row['id'],
                    defaults={
                        'username': row['username'],
                        'email': row['email'],
                        'role': row['role'],
                        'bio': row.get('bio', ''),
                        'first_name': row.get('first_name', ''),
                        'last_name': row.get('last_name', ''),
                    },
                )

    def import_categories(self):
        file_path = os.path.join(
            settings.BASE_DIR, 'static', 'data', 'category.csv'
        )
        with open(file_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                Category.objects.update_or_create(
                    id=row['id'],
                    defaults={
                        'name': row['name'],
                        'slug': row['slug'],
                    },
                )

    def import_genres(self):
        file_path = os.path.join(
            settings.BASE_DIR, 'static', 'data', 'genre.csv'
        )
        with open(file_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                Genre.objects.update_or_create(
                    id=row['id'],
                    defaults={
                        'name': row['name'],
                        'slug': row['slug'],
                    },
                )

    def import_titles(self):
        file_path = os.path.join(
            settings.BASE_DIR, 'static', 'data', 'titles.csv'
        )
        with open(file_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                category = Category.objects.filter(id=row['category']).first()
                title, created = Title.objects.update_or_create(
                    id=row['id'],
                    defaults={
                        'name': row['name'],
                        'year': int(row['year']),
                        'category': category,
                    },
                )

    def import_genre_title(self):
        file_path = os.path.join(
            settings.BASE_DIR, 'static', 'data', 'genre_title.csv'
        )
        with open(file_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                title = Title.objects.filter(id=row['title_id']).first()
                genre = Genre.objects.filter(id=row['genre_id']).first()
                if title and genre:
                    title.genre.add(genre)

    def import_reviews(self):
        file_path = os.path.join(
            settings.BASE_DIR, 'static', 'data', 'review.csv'
        )
        with open(file_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                author = UserProfile.objects.filter(id=row['author']).first()
                title = Title.objects.filter(id=row['title_id']).first()
                if author and title:
                    Review.objects.update_or_create(
                        id=row['id'],
                        defaults={
                            'author': author,
                            'title': title,
                            'score': int(row['score']),
                            'text': row['text'],
                            'pub_date': parse_datetime(row['pub_date']),
                        },
                    )

    def import_comments(self):
        file_path = os.path.join(
            settings.BASE_DIR, 'static', 'data', 'comments.csv'
        )
        with open(file_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                author = UserProfile.objects.filter(id=row['author']).first()
                review = Review.objects.filter(id=row['review_id']).first()
                if author and review:
                    Comment.objects.update_or_create(
                        id=row['id'],
                        defaults={
                            'author': author,
                            'review': review,
                            'text': row['text'],
                            'pub_date': parse_datetime(row['pub_date']),
                        },
                    )
