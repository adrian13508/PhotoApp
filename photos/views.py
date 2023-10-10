from django.http import HttpResponse, HttpResponseRedirect
from photos.models import Photo, Thumbnail
from photos.serializers import PhotoSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from PIL import Image
from django.conf import settings
import os
from rest_framework.generics import CreateAPIView, DestroyAPIView, GenericAPIView
from rest_framework import status
from cryptography.fernet import Fernet
import time
from rest_framework import serializers
from drf_spectacular.utils import extend_schema, OpenApiExample, inline_serializer
import environ

env = environ.Env()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

key = env('KEY')

def thumbnail_generation(request, serializer):
    access_tier = request.user.access_level
    thumbnails = Thumbnail.objects.filter(access_tier=access_tier)

    for photo in serializer:
        thumbnail_links = {}
        if access_tier.original_links:
            photo['original_link'] = photo['image']

        for thumbnail in thumbnails:
            relative_path = photo['image'].split(settings.MEDIA_URL, 1)
            local_path = os.path.join(settings.MEDIA_ROOT, relative_path[1])
            try:
                image = Image.open(local_path)
                size = (thumbnail.width, thumbnail.height)
                image.thumbnail(size)
                image.save(os.path.join(
                    settings.MEDIA_ROOT,
                    f'user_{request.user.username}',
                    photo['name'] + '_' + thumbnail.name + '.png'))
            except Exception as e:
                print(f"Error generating thumbnail for {photo['name']}: {str(e)}")

            if photo['expiring_links'] and access_tier.expiring_links:
                f = Fernet(key)
                current_time = int(time.time())
                token = f.encrypt_at_time(f'user_{request.user.username}/{photo["name"]}_{thumbnail.name}.png'.encode(),
                                          current_time)
                thumbnail_link = f'{relative_path[0]}/download/{token.decode()}'
                thumbnail_links[thumbnail.name] = thumbnail_link

            elif photo['expiring_links'] and access_tier.expiring_links is False:
                thumbnail_links[
                    thumbnail.name] = "You don't have access to generate expiring links, contact Admin to upgrade access tier"

            else:
                thumbnail_link = f'{relative_path[0]}{settings.MEDIA_URL}user_{request.user.username}/{photo["name"]}_{thumbnail.name}.png'
                thumbnail_links[thumbnail.name] = thumbnail_link
        photo['thumbnail_links'] = thumbnail_links
    return serializer


def docs_response(name):
    responses = {
        200: inline_serializer(
            name=name,
            fields={
                "id": serializers.IntegerField(required=False),
                "name": serializers.CharField(required=False),
                "created_at": serializers.DateField(required=False),
                "expiring_links": serializers.BooleanField(required=False),
                "original_link": serializers.CharField(required=False),
                "thumbnail_links": inline_serializer(
                    name='ThumbnailLinks',
                    fields={
                        "thumbnail_name": serializers.CharField(required=False),
                    },
                    required=False
                )

            },
        )}
    return responses


@extend_schema(
    operation_id='Generate links',
    description="Returns list of User's photos with newly generated links",
    request=PhotoSerializer,
    responses=docs_response('Generate links Response'),
    examples=[
        OpenApiExample(
            name='Links Response',
            value={
                "id": 0,
                "name": "string",
                "created_at": "2023-10-08",
                "expiring_links": False,
                "original_link": "string",
                "thumbnail_links": {
                    "small": "string",
                    "large": "string"
                }
            },
            response_only=True
        ),
    ]
)
class GenerateLinksView(GenericAPIView):
    """
    Returns photos with links generated.
    """
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [BrowsableAPIRenderer, JSONRenderer]

    def get(self, request):
        photos = Photo.objects.filter(user=request.user)
        serializer = PhotoSerializer(photos, many=True, context={'request': request})

        for photo in serializer.data:
            photo['expiring_links'] = False

        thumbnail_generation(request, serializer.data)

        for item in serializer.data:
            item.pop('image')
            item.pop('expiring_links')

        return Response(serializer.data)


@extend_schema(
    operation_id='Generate expiring links',
    description="Returns list of User's photos with newly generated expiring links",
    request=PhotoSerializer,
    responses=docs_response('Generate expiring links Response'),
    examples=[
        OpenApiExample(
            name='Expiring links Response',
            value={
                "id": 0,
                "name": "string",
                "created_at": "2023-10-08",
                "expiring_links": True,
                "original_link": "string",
                "thumbnail_links": {
                    "small": "string",
                    "large": "string"
                }
            },
            response_only=True

        ),
    ]
)
class GenerateExpiredLinksView(GenericAPIView):
    """
    Returns photos with expiring links generated.
    """
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [BrowsableAPIRenderer, JSONRenderer]

    def get(self, request):
        photos = Photo.objects.filter(user=request.user)
        serializer = PhotoSerializer(photos, many=True, context={'request': request})

        for photo in serializer.data:
            photo['expiring_links'] = True

        thumbnail_generation(request, serializer.data)

        for item in serializer.data:
            item.pop('image')
            item.pop('expiring_links')

        return Response(serializer.data)


@extend_schema(
    operation_id='Photo List',
    description="Returns list of User's uploaded photos.",
    request=PhotoSerializer,
    responses={
        200: inline_serializer(
            name='PasscodeResponse',
            fields={
                'id': serializers.IntegerField(required=False),
                'name': serializers.CharField(required=False),
                'created_at': serializers.DateField(required=False),

            }
        ),
    },
    examples=[
        OpenApiExample(
            name='photoList',
            value={
                "id": 0,
                "name": "string",
                "created_at": "2023-10-08",
            }
        )]
)
class PhotosListView(GenericAPIView):
    """
    Returns list of User's uploaded photos.
    """
    serializer_class = PhotoSerializer
    queryset = Photo.objects.all()
    permission_classes = [IsAuthenticated]
    renderer_classes = [BrowsableAPIRenderer, JSONRenderer]

    def get(self, request):
        queryset = Photo.objects.filter(user=request.user)
        serializer = PhotoSerializer(queryset, many=True, context={'request': request})

        # Remove the 'image' field from the response
        for item in serializer.data:
            item.pop('image')
            item.pop('expiring_links')

        return Response(serializer.data)


@extend_schema(
    operation_id='Photo upload',
    description='Upload Your photo and receive links for thumbnails.',
    request={
        "multipart/form-data": PhotoSerializer},
    methods=['POST'],
    responses=docs_response('Photo upload Response'),
    examples=[
        OpenApiExample(

            name='Sample Response',
            value={
                "id": 0,
                "name": "string",
                "created_at": "2023-10-08",
                "expiring_links": True,
                "original_link": "string",
                "thumbnail_links": {
                    "small": "string",
                    "large": "string"
                }
            },
            response_only=True

        ),
    ]

)
class UploadPhotoView(CreateAPIView):
    """
    Upload Your photo and receive links for thumbnails.

    If You select 'expiring_links' checkbox, You will receive expiring links for thumbnails.
    """
    queryset = Photo.objects.none()
    serializer_class = PhotoSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [BrowsableAPIRenderer, JSONRenderer]

    def create(self, request, *args, **kwargs):
        photo_data = {
            'name': request.data.get('name'),
            'image': request.data.get('image'),
            'expiring_links': request.data.get('expiring_links') or False
        }

        serializer = self.get_serializer(data=photo_data)

        if serializer.is_valid():
            photo = serializer.save(user=request.user)
            response_data = [self.serializer_class(photo, context={'request': request}).data]
            response_data = thumbnail_generation(request, response_data)
            for item in response_data:
                item.pop('image')
            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    operation_id='Download from expiring link',
    description="Redirects to the photo if token is valid.",
    request=PhotoSerializer,
    responses={
        200: inline_serializer(
            name='Download Response',
            fields={
                'reason': serializers.CharField(required=False),
            }
        ),
        404: inline_serializer(
            name='Download Response Error',
            fields={
                'reason': serializers.CharField(required=False),
            }
        ),
    }
)
class DownloadView(GenericAPIView):
    serializer_class = PhotoSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [BrowsableAPIRenderer, JSONRenderer]

    def get(self, request, token):

        photos = Photo.objects.filter(user=request.user)
        serializer = PhotoSerializer(photos, many=True, context={'request': request})

        f = Fernet(key)
        access_tier = request.user.access_level
        try:
            encrypted_filename = f.decrypt(token.encode(), ttl=access_tier.expiration_time).decode()
        except Exception as e:
            print(f"Error is accessing photo: {str(e)}")
            return HttpResponse('Token has expired', status=404)

        return HttpResponseRedirect(f'{settings.MEDIA_URL}{encrypted_filename}')


@extend_schema(
    operation_id='Delete photo',
    description="Returns status 204 if photo was deleted successfully.",
    request=PhotoSerializer,
    responses={
        204: inline_serializer(
            name='DeletePhotoResponse',
            fields={
                'reason': serializers.CharField(required=False),
            }),
        404: inline_serializer(
            name='DeletePhotoResponseError',
            fields={
                'reason': serializers.CharField(required=False),
            })

    },
    examples=[
        OpenApiExample(
            name='DeletePhotoResponse',
            value={
                "reason": "Photo was deleted successfully"
            },
            response_only=True,
            status_codes=['204']
        ),
        OpenApiExample(
            name='DeletePhotoResponseError',
            value={
                "reason": "Photo not found"
            },
            response_only=True,
            status_codes=['404']
        )
    ]
)
class DeletePhotoView(DestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PhotoSerializer

    def get_queryset(self):
        queryset = Photo.objects.get(pk=self.kwargs['pk'])
        return queryset

    def destroy(self, request, *args, **kwargs):
        obj = self.get_queryset()
        self.perform_destroy(obj)

        return Response(status=status.HTTP_204_NO_CONTENT)
