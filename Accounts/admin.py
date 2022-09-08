from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import MCIVUser

admin.site.register(MCIVUser, UserAdmin)
