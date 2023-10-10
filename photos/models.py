from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return "user_{0}/{1}".format(instance.user.username, filename)


def validate_image_extension(value):
    valid_extensions = ['jpg', 'jpeg', 'png']
    extension = value.name.split('.')[-1].lower()
    if extension not in valid_extensions:
        raise ValidationError("Only JPG and PNG files are allowed.")


class AccessTier(models.Model):
    name = models.CharField(max_length=20)
    original_links = models.BooleanField()
    expiring_links = models.BooleanField()
    expiration_time = models.PositiveIntegerField(
        null=True,
        blank=True, verbose_name='Expiration time in seconds',
        validators=[
            MinValueValidator(300,
                              message='Expiration time must be at least 300 seconds.'),
            MaxValueValidator(30000,
                              message='Expiration time must be at most 30000 seconds.'),
        ])

    def __str__(self):
        return self.name


class Thumbnail(models.Model):
    name = models.CharField(max_length=20)
    width = models.IntegerField()
    height = models.IntegerField()
    access_tier = models.ForeignKey(AccessTier, default=None, on_delete=models.CASCADE, related_name='thumbnails')

    def __str__(self):
        return self.name


class User(AbstractUser):
    access_level = models.ForeignKey(AccessTier, default=None, on_delete=models.CASCADE, related_name='access_level',
                                     null=True)


class Photo(models.Model):
    name = models.CharField(max_length=50)
    image = models.ImageField(upload_to=user_directory_path, validators=[validate_image_extension])
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateField(auto_now_add=True)
    expiring_links = models.BooleanField(default=False)

    def __str__(self):
        return self.name
