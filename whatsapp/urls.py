from django.urls import path

from . import views

app_name = "whatsapp"

urlpatterns = [
    path('', views.index, name='index'),
    path('whatsapp_send', views.send, name='send'),
    path('delete_all_database', views.deleteAllDataBase, name='deleteAllDataBase'),
    path('whatsapp_send_dont_have_what', views.sendDontHaveWhat, name='sendDontHaveWhat'),
    path('whatsapp_send_have_what', views.sendHaveWhat, name='sendHaveWhat'),
    path('send_to_specific_number', views.sendToSpecificNumber, name='sendToSpecificNumber'),
    path('whatsapp_send_report', views.whatsappSendReport, name='whatsappSendReport'),
]
