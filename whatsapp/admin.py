from django.contrib import admin

# Register your models here.

from .models import DrPhoneNumber, SystemSetting

admin.site.register(DrPhoneNumber)
admin.site.register(SystemSetting)
