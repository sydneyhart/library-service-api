from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


def api_root(request):
    return JsonResponse({"documentation": "/api/docs/"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/books/", include("books.urls")),
    path("api/", api_root, name="api-root"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path("api-auth/", include("rest_framework.urls")),
]
