# notes/tests/test_content.py
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestListPage(TestCase):
    LIST_URL = reverse('notes:list')
    AUTHORS_NOTES = 11
    USERS_NOTES = 2

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='testUser')
        cls.author = User.objects.create(username='Автор заметки')
        Note.objects.bulk_create(
            Note(
                title=f'Заметка автора №{index}',
                text='Просто текст.',
                slug=f'Sample_author_{index}',
                author=cls.author,
            )
            for index in range(cls.AUTHORS_NOTES)
        )
        Note.objects.bulk_create(
            Note(
                title=f'Заметка пользователя №{index}',
                text='Просто текст.',
                slug=f'Sample_User_{index}',
                author=cls.user,
            )
            for index in range(cls.USERS_NOTES)
        )

    def test_news_count(self):
        users_counts = (
            (self.author, self.AUTHORS_NOTES),
            (self.user, self.USERS_NOTES),
        )
        for user, count in users_counts:
            with self.subTest(user=user, count=count):
                self.client.force_login(user)
                response = self.client.get(self.LIST_URL)
                object_list = response.context['object_list']
                notes_count = object_list.count()
                self.assertEqual(notes_count, count)
