# notes/tests/test_logic.py
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from pytils.translit import slugify

from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):
    NOTE_TITLE = 'Заголовок заметки'
    NOTE_TEXT = 'Текст заметки'
    WARNING = ' - такой slug уже существует, придумайте уникальное значение!'

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='testUser')
        cls.author = User.objects.create(username='Автор заметки')
        cls.url = reverse('notes:add', args=None)
        # логинимся в клиенте.
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.author)
        # Данные для POST-запроса при создании комментария.
        cls.form_data = {
            'title': cls.NOTE_TITLE,
            'text': cls.NOTE_TEXT,
            'slug': 'sample',
        }

    def test_anonymous_user_cant_create_note(self):
        # Совершаем запрос от анонимного клиента, в POST-запросе отправляем
        # предварительно подготовленные данные формы с текстом комментария.
        self.client.post(self.url, data=self.form_data)
        # Считаем количество комментариев.
        notes_count = Note.objects.count()
        # Ожидаем, что комментариев в базе нет - сравниваем с нулём.
        self.assertEqual(notes_count, 0)

    def test_user_can_create_note(self):
        # Совершаем запрос через авторизованный клиент.
        self.auth_client.post(self.url, data=self.form_data)
        # Считаем количество записей.
        notes_count = Note.objects.count()
        # Убеждаемся, что есть один комментарий.
        self.assertEqual(notes_count, 1)
        # Получаем объект комментария из базы.
        note = Note.objects.get()
        # Проверяем, что все атрибуты комментария совпадают с ожидаемыми.
        self.assertEqual(note.title, self.NOTE_TITLE)
        self.assertEqual(note.text, self.NOTE_TEXT)
        self.assertEqual(note.author, self.author)

    def test_unique_slug(self):
        # Совершаем запрос через авторизованный клиент.
        self.auth_client.post(self.url, data=self.form_data)
        # Считаем количество записей.
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        # Повторяем запрос с теми же значениями полей формы
        response = self.auth_client.post(self.url, data=self.form_data)
        # Проверяем, есть ли в ответе ошибка формы.
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=f"{self.form_data['slug']}{self.WARNING}"
        )
        # Дополнительно убедимся, что комментарий не был создан.
        comments_count = Note.objects.count()
        self.assertEqual(comments_count, 1)

    def test_slugify(self):
        self.notes = Note.objects.create(
            title=self.NOTE_TITLE,
            text=self.NOTE_TEXT,
            author=self.author
        )
        note = Note.objects.get()
        self.assertEqual(note.slug, slugify(self.NOTE_TITLE))


class TestNoteDelete(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='testUser')
        cls.user_client = Client()
        cls.user_client.force_login(cls.user)
        cls.author = User.objects.create(username='Автор заметки')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.notes = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='sample',
            author=cls.author
        )
        # URL для удаления комментария.
        cls.delete_url = reverse('notes:delete', args=(cls.notes.slug,))

    def test_author_can_delete_note(self):
        # От имени автора комментария отправляем DELETE-запрос на удаление.
        self.author_client.delete(self.delete_url)
        # Считаем количество комментариев в системе.
        notes_count = Note.objects.count()
        # Ожидаем ноль комментариев в системе.
        self.assertEqual(notes_count, 0)

    def test_user_cant_delete_comment_of_another_user(self):
        # Выполняем запрос на удаление от пользователя-читателя.
        response = self.user_client.delete(self.delete_url)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Убедимся, что комментарий по-прежнему на месте.
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
