from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from users.models import User


class BaseAPITestCase(TestCase):
    """Базовый класс для инициализации клиента и тестовых данных."""

    def setUp(self):
        self.client = APIClient()

        self.user_password = "password123"
        self.user = User.objects.create_user(
            email="user@example.com", password=self.user_password, phone="+79991112233", city="Москва"
        )

        self.admin_password = "adminpass123"
        self.admin = User.objects.create_superuser(email="admin@example.com", password=self.admin_password)


class RegisterViewTests(BaseAPITestCase):
    def test_successful_registration(self):
        url = reverse("api:register")
        data = {
            "email": "newuser@example.com",
            "password": "StrongPass!123",
            "phone": "+79001112233",
            "city": "Санкт-Петербург",
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(email="newuser@example.com").exists())

    def test_duplicate_email(self):
        url = reverse("api:register")
        data = {"email": "user@example.com", "password": "AnotherPass123"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "Пользователь с таким Email уже существует.")


class AuthTokenTests(BaseAPITestCase):
    def test_obtain_token_with_valid_credentials(self):
        url = reverse("api:token_obtain_pair")
        data = {"email": self.user.email, "password": self.user_password}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)


class UserViewSetTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.other_user = User.objects.create_user(email="other@example.com", password="otherpass123")

    def test_regular_user_can_only_see_own_profile(self):
        token_url = reverse("api:token_obtain_pair")
        tokens = self.client.post(
            token_url, {"email": self.user.email, "password": self.user_password}, format="json"
        ).data

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')

        list_url = reverse("api:user-list")
        detail_url = reverse("api:user-detail", args=[self.other_user.pk])

        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.user.id)

        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 404)

    def test_admin_can_manage_everyone(self):
        token_url = reverse("api:token_obtain_pair")
        tokens = self.client.post(
            token_url, {"email": self.admin.email, "password": self.admin_password}, format="json"
        ).data

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')

        list_url = reverse("api:user-list")
        delete_url = reverse("api:user-detail", args=[self.user.pk])

        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 3)

        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())

    def test_regular_user_cannot_delete(self):
        token_url = reverse("api:token_obtain_pair")
        tokens = self.client.post(
            token_url, {"email": self.user.email, "password": self.user_password}, format="json"
        ).data

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')

        delete_url = reverse("api:user-detail", args=[self.other_user.pk])

        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, 403)
