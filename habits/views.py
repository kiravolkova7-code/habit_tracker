from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Habit
from .serializers import HabitSerializer
from .paginators import HabitPagination
from users.permissions import IsHabitOwner, CanCreateHabit
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.generics import ListAPIView


class HabitViewSet(viewsets.ModelViewSet):
    serializer_class = HabitSerializer
    pagination_class = HabitPagination

    def get_permissions(self):
        if self.action == "create":
            permission_classes = [CanCreateHabit]
        elif self.action in ["retrieve", "update", "partial_update", "destroy"]:
            permission_classes = [IsHabitOwner]
        else:
            permission_classes = [CanCreateHabit]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Базовый queryset используется только для детальных операций (retrieve/update/delete).
        """
        return Habit.objects.all()

    def list(self, request, *args, **kwargs):
        """
        GET /habits/
        """
        user_habits = Habit.objects.filter(user=request.user)

        page = self.paginate_queryset(user_habits)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(user_habits, many=True)
        return Response(serializer.data)

    def perform_update(self, serializer):
        try:
            instance = serializer.save(user=self.request.user)
            instance.full_clean()
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)

    def perform_create(self, serializer):
        """Для создания тоже лучше использовать full_clean для единообразия"""
        try:
            instance = serializer.save(user=self.request.user)
            instance.full_clean()
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PublicHabitListView(ListAPIView):
    """
    Отдельное представление ТОЛЬКО для публичных привычек.
    """

    queryset = Habit.objects.filter(is_public=True)
    serializer_class = HabitSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_authenticated:
            qs = qs.exclude(user=self.request.user)
        return qs
