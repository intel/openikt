from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from .models import *
from django.db.models import Q
from lib.jenkinswrapper import JenkinsWrapper
from app_diff.methods import format_resp
# Create your views here.


class GetOSImageView(APIView):
    """
    Summary
        get all os image

    Returns:
        image list
    """

    def get(self, request):
        os_image = ImageDiff.objects.all()
        ser = OSImageSerializers(instance=os_image, many=True)
        return Response(data=format_resp(data=ser.data), status=status.HTTP_200_OK)


class GetOSImageDataView(APIView):
    """
    Summary
        get all os image

    Returns:
        image list
    """
    def get(self, request):
        os_image = OSImage.objects.all()
        ser = OSImageListSerializers(instance=os_image, many=True)
        return Response(data=format_resp(data=ser.data), status=status.HTTP_200_OK)


class GetOSImageListView(APIView):
    """
    Summary
        get all os image by image id

    Returns:
        image list
    """
    def get(self, request):
        imageId = request.query_params.get("imageId")
        query = Q()
        if imageId:
            query = query & Q(id=imageId)
        os_image = ImageDiff.objects.select_related("img_a", "img_b")
        images = os_image.filter(query)
        ser = ImageListSerializers(instance=images, many=True)
        return Response(data=format_resp(data={"tableData": ser.data}), status=status.HTTP_200_OK)


class OSListView(APIView):
    """
    Summary:
        get os image type api view

    Return:
        the list of os image type data
    """

    def get(self, request):
        """get os image type api"""
        osType = [
            {"label": i[1], "value": i[0]} for i in PKGSection.OS_CHOICES
        ]
        return Response(data=format_resp(data=osType), status=status.HTTP_200_OK)


class PKGTypesView(APIView):
    """
    Summary:
        get os image type api view

    Return:
        the list of os image type data
    """

    def get(self, request):
        """get package type api"""
        pkgType = [
            {"label": i[1], "value": i[0]} for i in PKGRelation.TYPE_CHOICES
        ]
        return Response(data=format_resp(data=pkgType), status=status.HTTP_200_OK)


class ImportImageView(APIView):
    """
    Summary:
        import and diff image
    """

    def post(self, request, *args, **kwargs):
        data = request.data
        img_a = self.judge_import(img=data.get('imgA'))
        img_b = self.judge_import(img=data.get('imgB'))
        job = JenkinsWrapper(server_name='cje_jenkins')
        job.trigger_job(name='image-inspector', group='OpenIKT', data={'img_a': img_a, 'img_b': img_b})
        return Response(data=format_resp(data={}), status=status.HTTP_200_OK)

    @staticmethod
    def judge_import(img):
        '''
        add a new os image
        '''
        if img.get('isImport'):
            values = img.get('value')
            raw_data = values.get('rawData')
            os_img_obj = OSImage(
                os = values.get('os'),
                name = values.get('name'),
                release = values.get('release'),
                desc = values.get('desc'),
            )
            if raw_data:
                my_dir = os.path.dirname(os.path.abspath(__file__))
                raw_data_patch = 'raw_data/'
                image_name = raw_data
                file_name = os.path.join(my_dir, raw_data_patch, image_name)
                with open(file_name, 'r') as f:
                    os_img_obj.raw_data = f.read()
            else:
                os_img_obj.url = values.get('url')
            os_img_obj.save()
            return os_img_obj.name
        else:
            return img['value']


class RawDataUploadView(APIView):
    """
    Summary:
        uplaod raw data
    """

    def post(self, request, *args, **kwargs):
        html_file = request.FILES.get('file')
        image_name = request.data.get('imageName')
        my_dir = os.path.dirname(os.path.abspath(__file__))
        raw_data_patch = 'raw_data/'
        file_name = os.path.join(my_dir, raw_data_patch, image_name)
        with open(file_name, 'wb+') as destination:
            for chunk in html_file.chunks():
                destination.write(chunk)
        return Response(data=format_resp(data={}), status=status.HTTP_200_OK)


class ImageNameVerify(APIView):
    """
    Summary:
        verify name name unique
    """

    def get(self, request, *args, **kwargs):
        name = request.query_params.get('name')
        os_image = OSImage.objects.filter(name=name)
        if os_image:
            return Response(False, status=status.HTTP_200_OK)
        return Response(True, status=status.HTTP_200_OK)


class ImageDiffPackage(APIView):
    """
    Summary:
        get all image diff package
    """

    def get(self, request, *args, **kwargs):
        diff_id = request.query_params.get('DiffId')
        package_name = request.query_params.get('packageName')
        package_type = request.query_params.get('diffType')

        query = Q(imgdiff_id=diff_id)
        if package_name:
            query_p = Q(pkg_a__name__icontains=package_name) | Q(pkg_b__name__icontains=package_name)
            query = query & query_p
        if package_type:
            pkg_t = package_type.split(',')
            print(pkg_t)
            query = query & Q(pkgtype__in=pkg_t)
        image_diff_pag = ImageDiffPKG.objects.filter(query).order_by('pkgtype', 'pkg_a__name')
        ser = ImageDiffPkgSerializers(instance=image_diff_pag, many=True)
        return Response(data=format_resp(data={"tableData": ser.data}), status=status.HTTP_200_OK)


class PKGDetail(APIView):
    """
    Summary:
        get one image diff package detail
    """

    def get(self, request, *args, **kwargs):
        pkg_id = request.query_params.get('PackageId')
        pkgs = Package.objects.filter(id=pkg_id)
        ser = PkgdetailSerializers(instance=pkgs, many=True)
        return Response(data=format_resp(data=ser.data), status=status.HTTP_200_OK)