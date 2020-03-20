from django.urls import include, path
from rest_framework.documentation import include_docs_urls


urlpatterns = [
    path('v1/call-records/', include('records.urls')),
    path('v1/docs/', include_docs_urls(title='Library API Project'))
]
