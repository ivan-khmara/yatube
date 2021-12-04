import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskFormTests(TestCase):
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(TaskFormTests.user)

    def test_create_post(self):
        """ Проверка: Отправка валидной формы с картиной со страницы создания поста
        создает запись в Post."""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        post_count_start = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост для проверки валидной формы',
            'group': TaskFormTests.group.id,
            'author': TaskFormTests.user,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            reverse('posts:profile', args=[TaskFormTests.user.username])
        )
        self.assertEqual(Post.objects.count(), post_count_start + 1)
        post = Post.objects.latest("pub_date")
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author, form_data['author'])
        self.assertEqual(post.image,
                         f"posts/{form_data['image']}")

    def test_edit_post(self):
        """ Проверка: Отправка валидной формы со станицы редактирования поста
        изменяет пост в базе данных."""
        post_id = TaskFormTests.post.id
        form_data = {
            'text': 'измененный тестовый пост',
            'group': TaskFormTests.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=[post_id]),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', args=[post_id])
        )
        change_post = Post.objects.get(pk=post_id)
        self.assertEqual(change_post.text, form_data['text'])
        self.assertEqual(change_post.group.id, form_data['group'])

    def test_create_post_guest_client(self):
        """ Проверка: Создание поста неавторизованным пользователем."""
        post_count_start = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост для проверки валидной формы',
            'group': TaskFormTests.group.id,
            'author': TaskFormTests.user
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            reverse('users:login') + '?next=' + reverse('posts:post_create')
        )
        self.assertEqual(Post.objects.count(), post_count_start)

    def test_create_comment(self):
        """ Проверка: Создание комментария."""
        comment_count_start = TaskFormTests.post.comments.all().count()
        post_id = TaskFormTests.post.id
        form_data = {
            'post': TaskFormTests.post,
            'author': TaskFormTests.user,
            'text': 'Тестовый комментарий',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', args=[post_id]),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            TaskFormTests.post.comments.all().count(),
            comment_count_start + 1
        )

    def test_create_comment_guest_client(self):
        """ Проверка: Создание комментария неавторизованным пользователем."""
        comment_count_start = TaskFormTests.post.comments.all().count()
        post_id = TaskFormTests.post.id
        form_data = {
            'post': TaskFormTests.post,
            'author': TaskFormTests.user,
            'text': 'Тестовый комментарий',
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', args=[post_id]),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            TaskFormTests.post.comments.all().count(),
            comment_count_start
        )
