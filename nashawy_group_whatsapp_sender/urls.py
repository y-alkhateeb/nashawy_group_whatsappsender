from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('', include('whatsapp.urls', namespace="whatsapp")),
    # path('whatsapp/', include('whatsapp.urls')),
    path('admin/', admin.site.urls),
]
