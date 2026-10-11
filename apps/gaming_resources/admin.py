from django.contrib import admin

from .models import Equipment, GalleryImage, OpeningHour, Station

admin.site.register(Equipment)
admin.site.register(Station)
admin.site.register(OpeningHour)
admin.site.register(GalleryImage)
