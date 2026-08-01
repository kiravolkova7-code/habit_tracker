from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class HabitPagination(PageNumberPagination):
    """
    Кастомный паджинатор для вывода списка привычек.
    """

    page_size = 5
    page_size_query_param = None
    max_page_size = 5

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "current_page": self.page.number,
                "total_pages": self.page.paginator.num_pages,
                "results": data,
            }
        )
