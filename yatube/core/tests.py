from http import HTTPStatus

from django.test import TestCase


class ViewTestClass(TestCase):
    def test_error_page(self):
        """Тест, проверяющий, что страница 404 отдает кастомный шаблон."""
        response = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        template = 'core/404.html'
        self.assertTemplateUsed(response, template)
