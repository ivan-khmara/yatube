from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='group_test',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        """ Создаем неавторизованный клиент"""
        self.guest_client = Client()
        """ Создаем авторизованый клиент"""
        self.authorized_client = Client()
        self.authorized_client.force_login(TaskURLTests.user)

    def test_status_code_authorized_client(self):
        """Проверка: доступность страниц для авторизированного пользователя"""
        url_names_status_code_authorized_client = {
            '/': 200,
            f'/group/{TaskURLTests.group.slug}/': HTTPStatus.OK,
            f'/profile/{TaskURLTests.user.username}/': HTTPStatus.OK,
            f'/posts/{int(TaskURLTests.post.id)}/': HTTPStatus.OK,
            f'/posts/{int(TaskURLTests.post.id)}/edit/': HTTPStatus.OK,
            '/create/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND
        }
        for url, code in url_names_status_code_authorized_client.items():
            with self.subTest(code=code):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, code)

    def test_status_code_guest_client(self):
        """Проверка: доступность страниц для гостя"""
        url_names_status_code_guest_client = {
            '/': 200,
            f'/group/{TaskURLTests.group.slug}/': HTTPStatus.OK,
            f'/profile/{TaskURLTests.user.username}/': HTTPStatus.OK,
            f'/posts/{int(TaskURLTests.post.id)}/': HTTPStatus.OK,
            f'/posts/{int(TaskURLTests.post.id)}/edit/': HTTPStatus.FOUND,
            '/create/': HTTPStatus.FOUND,
            '/unexisting_page/': HTTPStatus.NOT_FOUND
        }
        for url, code in url_names_status_code_guest_client.items():
            with self.subTest(code=code):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, code)

    def test_urls_uses_correct_template(self):
        """Проверка: URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{TaskURLTests.group.slug}/': 'posts/group_list.html',
            f'/profile/{TaskURLTests.user.username}/': 'posts/profile.html',
            f'/posts/{int(TaskURLTests.post.id)}/': 'posts/post_detail.html',
            f'/posts/{int(TaskURLTests.post.id)}/edit/':
                'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
