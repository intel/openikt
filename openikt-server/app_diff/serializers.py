from rest_framework import serializers
from app_diff.models import Repository, RangeDiff


class RepositorySerializers(serializers.ModelSerializer):
    """Repository serializers"""

    label = serializers.CharField(source="url")
    value = serializers.IntegerField(source="id")

    class Meta:
        model = Repository
        fields = ["label", "value"]


class QulitDiffTagsSerializers(serializers.ModelSerializer):
    """Qulit Diff Tags Serializers"""

    label = serializers.SerializerMethodField()
    value = serializers.IntegerField(source="id")

    class Meta:
        model = RangeDiff
        fields = ["label", "value"]

    def get_label(self, obj):
        """get refa and refb format data"""
        return f"{obj.ref_a} .. {obj.ref_b}"


class QulitDiffSerializers(serializers.ModelSerializer):
    """Qulit Diff Serializers"""

    diff_type = serializers.CharField(source="get_difftype_display")
    created_date = serializers.DateTimeField(format="%Y-%m-%d")
    repoA = serializers.SerializerMethodField()
    repoB = serializers.SerializerMethodField()

    class Meta:
        model = RangeDiff
        fields = [
            "id",
            "ref_a",
            "ref_b",
            "base_a",
            "base_b",
            "diff_type",
            "repoA",
            "repoB",
            "created_date",
        ]

    def get_repoA(self, obj):
        """format repo a data"""
        if obj.repo_a:
            return {"href": obj.repo_a.url(), "label": obj.repo_a.name}
        return ""

    def get_repoB(self, obj):
        """format repo b data"""
        if obj.repo_b:
            return {"href": obj.repo_b.url(), "label": obj.repo_b.name}
        return ""
