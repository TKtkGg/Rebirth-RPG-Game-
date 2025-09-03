from django.contrib import admin
from .models import Player, PlayerProfile,Enemy
# Register your models here.

admin.site.register(Player)
admin.site.register(PlayerProfile)
admin.site.register(Enemy)