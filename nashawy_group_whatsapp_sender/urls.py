from django.contrib import admin
from django.urls import include, path

from whatsapp.admin import admin_site

urlpatterns = [
    path('', include('whatsapp.urls', namespace="whatsapp")),
    # path('superadmin/', admin.site.urls),
    path('admin/', admin_site.urls)
]
