from django.contrib import admin
from .models import AccessTier, Thumbnail, User, Photo


class ThumbnailInline(admin.TabularInline):
    model = Thumbnail
    fields = ('name', 'width', 'height')


class AccessTierAdmin(admin.ModelAdmin):
    list_display = ('name', 'original_links', 'expiring_links', 'expiration_time')
    inlines = [ThumbnailInline]


@admin.register(Thumbnail)
class ThumbnailAdmin(admin.ModelAdmin):
    list_display = ('name', 'width', 'height', 'access_tier')


admin.site.register(User)
admin.site.register(Photo)
admin.site.register(AccessTier, AccessTierAdmin)
