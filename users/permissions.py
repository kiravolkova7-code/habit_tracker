from rest_framework import permissions


class IsHabitOwner(permissions.BasePermission):
    """
    Разрешает доступ только владельцу привычки к конкретному объекту.
    Используется для retrieve, update, destroy.
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class CanCreateHabit(permissions.BasePermission):
    """
    Разрешает создание привычек только авторизованным пользователям.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated