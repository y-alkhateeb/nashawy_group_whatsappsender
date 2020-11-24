from django.conf.urls import url
from django.urls import path

from . import views

app_name = "whatsapp"

urlpatterns = [
    path('', views.index, name='index'),
    path('whatsapp_send', views.send, name='send'),
    path('whatsapp_send_dont_have_what', views.sendDontHaveWhat, name='sendDontHaveWhat'),
    path('whatsapp_send_have_what', views.sendHaveWhat, name='sendHaveWhat'),
]
