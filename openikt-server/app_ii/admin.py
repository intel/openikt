from django.contrib import admin
from app_ii.models import *

# Register your models here.
admin.site.register(PKGSection)
admin.site.register(OSImage)
admin.site.register(Contributor)
admin.site.register(PKGContributor)
admin.site.register(Package)
admin.site.register(PKGExtraInfo)
admin.site.register(PKGRelation)
admin.site.register(ImageDiff)
admin.site.register(ImageDiffPKG)
