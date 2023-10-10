from rest_framework import serializers
from .models import Photo, AccessTier, Thumbnail


class AccessTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessTier
        fields = ('name', 'original_links', 'expiring_links')


class ThumbnailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Thumbnail
        fields = ('name', 'width', 'height')


class PhotoSerializer(serializers.ModelSerializer):
    expiring_links = serializers.BooleanField(required=False)

    class Meta:
        model = Photo
        fields = ('id', 'name', 'image', 'created_at', 'expiring_links')

        extra_kwargs = {
            'name': {'required': True},
            'image': {'required': True}
        }

