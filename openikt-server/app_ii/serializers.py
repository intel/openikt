from rest_framework import serializers
from app_ii.models import *


class OSImageSerializers(serializers.ModelSerializer):
    """OS image serializers"""

    label = serializers.SerializerMethodField()
    value = serializers.IntegerField(source="id")

    class Meta:
        model = ImageDiff
        fields = ["label", "value"]
    
    def get_label(self, obj):
        return str(obj)


class OSImageListSerializers(serializers.ModelSerializer):
    """OS image serializers"""

    label = serializers.CharField(source="name")
    value = serializers.IntegerField(source="id")

    class Meta:
        model = OSImage
        fields = ["label", "value"]


class ImageListSerializers(serializers.ModelSerializer):
    """image list Serializers"""

    created = serializers.DateTimeField(format="%Y-%m-%d")
    urlA = serializers.CharField(source="img_a.url")
    urlB = serializers.CharField(source="img_b.url")
    release_a = serializers.CharField(source="img_a.release")
    release_b = serializers.CharField(source="img_b.release")
    img_a = serializers.CharField(source="img_a.name")
    img_b = serializers.CharField(source="img_b.name")

    class Meta:
        model = ImageDiff
        fields = [
            "id",
            "img_a",
            "img_b",
            "release_a",
            "release_b",
            "urlA",
            "urlB",
            "created",
        ]


class ImageDiffPkgSerializers(serializers.ModelSerializer):
    
    pkg_type = serializers.CharField(source="get_pkgtype_display")
    pkg_a = serializers.SerializerMethodField()
    pkg_a_version = serializers.SerializerMethodField()
    pkg_b = serializers.SerializerMethodField()
    pkg_b_version = serializers.SerializerMethodField()
    
    class Meta:
        model = ImageDiffPKG
        fields = [
            'pkg_type',
            'pkg_a',
            'pkg_b',
            'pkg_a_version',
            'pkg_b_version',
        ]
    
    def get_pkg_a(self, obj):
        if obj.pkg_a:
            return {'name': obj.pkg_a.name, 'id':obj.pkg_a.id}
        return ""
    
    def get_pkg_a_version(self, obj):
        if obj.pkg_a:
            return obj.pkg_a.version
        return ""
    
    def get_pkg_b(self, obj):
        if obj.pkg_b:
            return {'name': obj.pkg_b.name, 'id':obj.pkg_b.id}
        return ""
    
    def get_pkg_b_version(self, obj):
        if obj.pkg_b:
            return obj.pkg_b.version
        return ""


class PkgdetailSerializers(serializers.ModelSerializer):
    arch = serializers.CharField(source="get_arch_display")
    img_name = serializers.CharField(source="image.name")
    section_info = serializers.SerializerMethodField()
    homepage = serializers.SerializerMethodField()
    source = serializers.SerializerMethodField()
    relation = serializers.SerializerMethodField()
    contributor = serializers.SerializerMethodField()
    
    class Meta:
        model = Package
        fields = [
            'name',
            'version',
            'summary',
            'desc',
            'homepage',
            'source',
            'arch',
            'img_name',
            'section_info',
            'relation',
            'contributor'
        ]
        
    def get_section_info(self, obj):
        if obj.section:
            return {
                'name': obj.section.name,
                'desc': obj.section.desc if obj.section.desc else '',
                'os': obj.section.get_os_display(),
            }
        return ""
    
    def get_homepage(self, obj):
        if obj.homepage:
            return obj.homepage
        return ""
    
    def get_source(self, obj):
        if obj.source:
            return obj.source
        return ""
    
    def get_relation(self, obj):
        pkg_relation = PKGRelation.objects.filter(package_id=obj.id)
        if pkg_relation:
            return [str(prl) for prl in pkg_relation]
        return []
    
    def get_contributor(self, obj):
        pkg_contributor = PKGContributor.objects.filter(package_id=obj.id)
        if pkg_contributor:
            return [str(pcb) for pcb in pkg_contributor]
        return []
    