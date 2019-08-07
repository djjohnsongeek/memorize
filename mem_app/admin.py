from django.contrib import admin

# Register your models here.
from .models import Verse, User_verses

admin.site.register(Verse)
admin.site.register(User_verses)
