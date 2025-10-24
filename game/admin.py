from django.contrib import admin
from .models import Player, Enemy, PlayerProfile, Equipment

admin.site.register(Player)
admin.site.register(Enemy)
admin.site.register(PlayerProfile)
admin.site.register(Equipment)