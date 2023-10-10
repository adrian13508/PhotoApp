from django.urls import path
from photos import views

urlpatterns = [
    path('photos/', views.PhotosListView.as_view()),
    path('photos/generate', views.GenerateLinksView.as_view()),
    path('photos/generateExpired', views.GenerateExpiredLinksView.as_view()),
    path('photos/add', views.UploadPhotoView.as_view()),
    path('photos/delete/<int:pk>', views.DeletePhotoView.as_view()),
    path('download/<str:token>', views.DownloadView.as_view()),
]