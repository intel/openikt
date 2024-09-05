from django.urls import path
from .views import *

urlpatterns = [
    path('refs', GetRefsView.as_view(), name='refs'),
    path('repos', GetRepositoryView.as_view(), name='repos'),
    path('quilt_diffs', QuiltDiffView.as_view(), name='quilt_diff'),
    path('detail', QuiltDiffDetailView.as_view(), name='quilt_diff_detail'),
    path('type', RangeDiffPatchTypeView.as_view(), name='quilt_diff_patch_type'),
    path('diff_type', RangeDiffTypeView.as_view(), name='quilt_diff_type'),
    path('create', TriggerDiffJob.as_view(), name='trigger_diff_job'),
]
