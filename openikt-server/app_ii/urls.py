from django.urls import path
from .views import *

urlpatterns = [
    path('os_list', OSListView.as_view(), name='os_list'),
    path('images', GetOSImageView.as_view(), name='images'),
    path('image_list', GetOSImageListView.as_view(), name='image_list'),
    path('image_data', GetOSImageDataView.as_view(), name='image_data'),
    path('create', ImportImageView.as_view(), name='import_os'),
    path('raw_data_upload', RawDataUploadView.as_view(), name='import_os'),
    path('name_verify', ImageNameVerify.as_view(), name='image_name_verify'),
    path('url_verify', ImageUrlVerify.as_view(), name='image_url_verify'),
    path('image_diff_pkg', ImageDiffPackage.as_view(), name='image_diff_pkg'),
    path('image_diff_pkg', ImageDiffPackage.as_view(), name='image_diff_pkg'),
    path('pkg_detail', PKGDetail.as_view(), name='pkg_detail'),
    path('pkg_type', PKGTypesView.as_view(), name='pkg_type'),
    path('diff_exist', JudgeImageDiff.as_view(), name='diff_exist'),
]