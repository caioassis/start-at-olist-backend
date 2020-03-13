from django.contrib import admin
from django.urls import include, path
from rest_framework.documentation import include_docs_urls


urlpatterns = [
    path('admin/', admin.site.urls),
    path('call_records/', include('records.urls')),
    path('docs/', include_docs_urls(title='Library API Project'))
]
