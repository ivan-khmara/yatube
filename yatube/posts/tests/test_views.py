import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from yatube.settings import COUNT_POSTS_PAGE as CPP

from ..models import Follow, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='no_autorized')
        cls.user_authorized = User.objects.create_user(username='autorized')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='group_test',
            description='Тестовое описание',
        )
        Post.objects.bulk_create([
            Post(text=f'Тестовый пост {str(i)}',
                 author=cls.user) for i in range(15)
        ])
        Post.objects.bulk_create([
            Post(text=f'Тестовый пост c группой {str(i)}',
                 author=cls.user, group=cls.group) for i in range(31)
        ])
        cls.post = Post.objects.create(
            author=cls.user_authorized,
            text='Тестовый пост c группой и новым user',
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(TaskViewTests.user_authorized)

    def test_pages_uses_correct_template(self):
        """ Проверка: во view-функциях используются правильные html-шаблоны"""
        templates_url_names_authorized = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', args=[TaskViewTests.group.slug]):
                'posts/group_list.html',
            reverse('posts:profile', args=[TaskViewTests.user.username]):
                'posts/profile.html',
            reverse('posts:post_detail', args=[int(TaskViewTests.post.id)]):
                'posts/post_detail.html',
            reverse('posts:post_edit', args=[int(TaskViewTests.post.id)]):
                'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_url_names_authorized.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_view_index(self):
        """ Проверка: список всех постов"""
        count_all_post = Post.objects.all().count()
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(
            len(response.context['page_obj']),
            min(CPP, count_all_post)
        )
        if count_all_post > CPP:
            response = self.guest_client.get(
                reverse('posts:index') + '?page='
                + str(count_all_post // CPP + 1)
            )
            self.assertEqual(
                len(response.context['page_obj']),
                count_all_post % CPP
            )

    def test_view_group_posts(self):
        """ Проверка: список постов отфильтрованный по группе"""
        count_group_post = Post.objects.filter(
            group=TaskViewTests.group).count()
        response = self.guest_client.get(
            reverse('posts:group_list', args=[TaskViewTests.group.slug])
        )
        self.assertEqual(
            len(response.context['page_obj']),
            min(CPP, count_group_post)
        )
        for post_test in response.context.get('page_obj').object_list:
            self.assertEqual(post_test.group.slug, TaskViewTests.group.slug)
        if count_group_post > CPP:
            response = self.guest_client.get(
                reverse('posts:group_list', args=[TaskViewTests.group.slug])
                + '?page=' + str(count_group_post // CPP + 1)
            )
            self.assertEqual(
                len(response.context['page_obj']),
                count_group_post % CPP
            )
            for post_test in response.context.get('page_obj').object_list:
                self.assertEqual(
                    post_test.group.slug,
                    TaskViewTests.group.slug
                )

    def test_view_profile(self):
        """ Проверка: список постов отфильтрованный по пользователю"""
        count_user_post = Post.objects.filter(
            author=TaskViewTests.user).count()
        response = self.guest_client.get(
            reverse('posts:profile', args=[TaskViewTests.user.username])
        )
        self.assertEqual(
            len(response.context['page_obj']),
            min(CPP, count_user_post)
        )
        for post_test in response.context.get('page_obj').object_list:
            self.assertEqual(
                post_test.author.username,
                TaskViewTests.user.username
            )
        if count_user_post > CPP:
            response = self.guest_client.get(
                reverse('posts:profile', args=[TaskViewTests.user.username])
                + '?page=' + str(count_user_post // CPP + 1)
            )
            self.assertEqual(
                len(response.context['page_obj']), count_user_post % CPP)
            for post_test in response.context.get('page_obj').object_list:
                self.assertEqual(
                    post_test.author.username,
                    TaskViewTests.user.username
                )

    def test_view_post_detail(self):
        """ Проверка: пост отфильтрованный по id"""
        response = self.guest_client.get(
            reverse('posts:post_detail', args=[int(TaskViewTests.post.id)]))
        self.assertEqual(
            response.context.get('post').id,
            int(TaskViewTests.post.id)
        )

    def test_view_post_create(self):
        """ Проверка: форма создания поста"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_view_post_edit(self):
        """ Проверка: форма редактирования поста отфильтрованного по id"""
        response = self.authorized_client.get(
            reverse('posts:post_edit', args=[int(TaskViewTests.post.id)])
        )
        form_fields = {
            'text': TaskViewTests.post.text,
            'group': TaskViewTests.post.group.id,
        }
        self.assertEqual(
            response.context.get('pk'),
            int(TaskViewTests.post.id)
        )
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].initial[value]
                self.assertEqual(form_field, expected)

    def test_new_post(self):
        count_group_post = Post.objects.filter(
            group=TaskViewTests.group).count()
        user = User.objects.create_user(username='test')
        group_new = Group.objects.create(
            title='Новая тестовая группа',
            slug='group_test_new',
            description='Тестовое описание',
        )
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
        post_new = Post.objects.create(
            author=user,
            text='Временный пост с временным пользоваелем и временной группой',
            group=group_new,
            image=uploaded
        )
        """ Проверка: на главной странице сайта,"""
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(response.context['page_obj'][0].text, post_new.text)
        self.assertEqual(response.context['page_obj'][0].image, post_new.image)
        """ Проверка: на странице временной группы,"""
        response = self.guest_client.get(
            reverse('posts:group_list', args=[group_new.slug])
        )
        self.assertEqual(len(response.context['page_obj']), 1)
        self.assertEqual(post_new.group.slug, group_new.slug)
        self.assertEqual(response.context['page_obj'][0].image, post_new.image)
        """ Проверка: в профайле временного пользователя"""
        response = self.guest_client.get(
            reverse('posts:profile', args=[user.username])
        )
        self.assertEqual(len(response.context['page_obj']), 1)
        self.assertEqual(post_new.author.username, user.username)
        self.assertEqual(response.context['page_obj'][0].image, post_new.image)
        """ Проверка: пост не попал в группу,
        для которой не был предназначен"""
        response = self.guest_client.get(
            reverse('posts:group_list', args=[TaskViewTests.group.slug])
            + '?page=' + str(count_group_post // CPP + 1)
        )
        self.assertEqual(
            len(response.context['page_obj']),
            count_group_post % CPP
        )
        """ Проверка: картинка передается на отдельную страницу поста"""
        response = self.guest_client.get(
            reverse('posts:post_detail', args=[post_new.id]))
        self.assertEqual(response.context.get('post').id, post_new.id)
        self.assertEqual(response.context.get('post').image, post_new.image)

    def test_follow_unfollow(self):
        """ Проверка: Авторизованный пользователь может подписываться
        на других пользователей и удалять их из подписок."""
        user_author = TaskViewTests.user
        user_authorized = TaskViewTests.user_authorized
        count_following = user_author.following.all().count()
        count_follower = user_authorized.follower.all().count()
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            args=[user_author.username])
        )
        self.assertEqual(
            user_author.following.all().count(),
            count_following + 1
        )
        self.assertEqual(
            user_authorized.follower.all().count(),
            count_follower + 1
        )
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            args=[user_author.username])
        )
        self.assertEqual(
            user_author.following.all().count(),
            count_following
        )
        self.assertEqual(
            user_authorized.follower.all().count(),
            count_follower
        )

    def test_follow_index(self):
        """ Проверка: Новая запись пользователя появляется в ленте тех, кто
        на него подписан и не появляется в ленте тех, кто не подписан."""
        user_no_follower = TaskViewTests.user
        user_follower = TaskViewTests.user_authorized
        user = User.objects.create_user(username='test')
        Follow.objects.create(user=user_follower, author=user)
        self.authorized_client.force_login(user_follower)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        user_follower_count_post = len(response.context['page_obj'])
        self.authorized_client.force_login(user_no_follower)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        user_no_follower_count_post = len(response.context['page_obj'])
        post_new = Post.objects.create(
            author=user,
            text='Временный пост для подписок',
        )
        self.authorized_client.force_login(user_follower)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(
            len(response.context['page_obj']),
            user_follower_count_post + 1
        )
        self.assertEqual(response.context['page_obj'][0].text, post_new.text)
        self.authorized_client.force_login(user_no_follower)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(
            len(response.context['page_obj']),
            user_no_follower_count_post
        )
