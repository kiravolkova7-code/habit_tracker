from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from .models import Habit

User = get_user_model()


class BaseTestSetup(APITestCase):
    """Базовый класс с данными для всех тестов."""

    def setUp(self):
        self.user1 = User.objects.create_user(email="user1@test.com", password="password123")
        self.user2 = User.objects.create_user(email="user2@test.com", password="password123")

        self.habit1 = Habit.objects.create(
            user=self.user1, action="Почитать книгу", time="в 21:00", location="в кровати", is_public=False
        )

        self.pleasant_habit = Habit.objects.create(
            user=self.user1, action="Выпить чаю с медом", is_pleasant=True, is_public=False
        )

        self.linked_habit = Habit.objects.create(
            user=self.user1, action="Сделать зарядку", pleasant_habit=self.pleasant_habit, is_public=False
        )

        self.public_habit = Habit.objects.create(user=self.user2, action="Пройти 5000 шагов", is_public=True)

        self.list_url = reverse("habits:habit-list")
        self.detail_url_1 = reverse("habits:habit-detail", args=[self.habit1.id])
        self.public_url = reverse("habits:public-habits")


class HabitOwnerAPITests(BaseTestSetup):
    """Тесты CRUD-прав владельца и бизнес-логики."""

    def test_create_habit_success(self):
        """Создание полезной привычки без награды."""
        self.client.force_authenticate(user=self.user1)
        data = {
            "action": "Выпить стакан воды",
            "time": "в 08:00",
            "location": "на кухне",
            "estimated_duration_seconds": 60,
            "periodicity_days": 1,
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(Habit.objects.get(id=response.data["id"]).is_pleasant)

    def test_create_with_both_rewards_fails(self):
        """Нельзя указать текстовое вознаграждение и приятную привычку одновременно."""
        self.client.force_authenticate(user=self.user1)
        data = {
            "action": "Тест",
            "reward_description": "Конфета",
            "pleasant_habit": self.pleasant_habit.id,
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn("reward_description", response.data)
        self.assertIn("pleasant_habit", response.data)

    def test_cannot_link_unpleasant_habit(self):
        """В связанную привычку можно выбрать только ту, где is_pleasant=True."""
        self.client.force_authenticate(user=self.user1)
        bad_habit = Habit.objects.create(user=self.user1, action="Обычная привычка", is_pleasant=False)
        data = {"action": "Связь", "pleasant_habit": bad_habit.id}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("pleasant_habit", response.data)

    def test_periodicity_validation(self):
        """Проверка периодичности от 1 до 7 дней."""
        self.client.force_authenticate(user=self.user1)
        data = {"action": "Редкое действие", "periodicity_days": 14}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("periodicity_days", response.data)

    def test_owner_can_delete(self):
        """Владелец может удалить свою привычку."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(self.detail_url_1)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Habit.objects.filter(id=self.habit1.id).exists())

    def test_non_owner_cannot_delete(self):
        """Другой пользователь не может удалить чужую привычку."""
        self.client.force_authenticate(user=self.user2)
        response = self.client.delete(self.detail_url_1)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PublicAndListAPITests(BaseTestSetup):
    """Тесты списков привычек (свои vs публичные)."""

    def test_list_returns_only_users_habits(self):
        """Список /habits/ возвращает ТОЛЬКО привычки залогиненного пользователя."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ids = [item["id"] for item in response.data["results"]]
        self.assertIn(self.habit1.id, ids)
        self.assertNotIn(self.public_habit.id, ids)

    def test_public_habits_endpoint(self):
        """Эндпоинт /habits/public/ возвращает только чужие публичные привычки."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.public_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ids = [item["id"] for item in response.data["results"]]
        self.assertIn(self.public_habit.id, ids)
        self.assertNotIn(self.habit1.id, ids)

    def test_public_habits_anonymous(self):
        """Доступ к публичным привычкам есть у анонимных пользователей."""
        response = self.client.get(self.public_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_pagination_limit(self):
        """Проверка паджинации (5 элементов на страницу из settings)."""

        for i in range(10):
            Habit.objects.create(user=self.user1, action=f"Привычка {i}")

        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 5)
        self.assertIsNotNone(response.data["next"])
