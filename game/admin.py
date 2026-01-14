from django.contrib import admin
from .models import Player, Enemy, Equipment, Item, Stage

admin.site.register(Player)
admin.site.register(Enemy)
admin.site.register(Equipment)
admin.site.register(Item)
admin.site.register(Stage)