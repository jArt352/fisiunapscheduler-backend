from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    page_size = 15  # Número de elementos por página
    page_size_query_param = "page_size"
    max_page_size = 10000  # Número máximo de elementos por página
