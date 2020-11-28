from django.contrib import admin

# Register your models here.
from django.contrib.admin import AdminSite
from django.contrib.auth.models import User
from .models import DrPhoneNumber, SystemSetting, SystemReporting, PhoneNumberGroup


class MyAdminSite(AdminSite):
    site_header = 'Nashawy group whatsapp sender'


class DrPhoneNumberAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'number_of_message_sent', 'have_whatsapp', 'group', 'note')
    list_filter = ('group_id', 'number_of_message_sent', 'have_whatsapp')
    search_fields = ('phone_number', 'number_of_message_sent')


class SystemReportingAdmin(admin.ModelAdmin):
    list_display = ('total_success_sent', 'total_failure_sent', 'date_of_reporting')
    list_filter = ['date_of_reporting']


class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ('last_index_sent', 'type_sent', 'last_phone_number', 'last_date_of_sent')


admin_site = MyAdminSite(name='admin')
admin_site.register(DrPhoneNumber, DrPhoneNumberAdmin)
admin_site.register(SystemSetting, SystemSettingAdmin)
admin_site.register(SystemReporting, SystemReportingAdmin)
admin_site.register(PhoneNumberGroup)
admin_site.register(User)
