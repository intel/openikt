from django.contrib import admin
from app_diff.models import *

# Register your models here.
admin.site.register(Repository)
admin.site.register(UpstreamedPatch)
admin.site.register(RangeDiff)
admin.site.register(RangeDiffPatch)
admin.site.register(PR)
