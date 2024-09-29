from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
from django.http import JsonResponse
from .serializers import *
from .models import *
from django.db.models import Q
from lib.jenkinswrapper import JenkinsWrapper
from lib.email import send_email
from app_diff.methods import format_resp
from django.contrib.auth.models import AnonymousUser
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
        os_image = OSImage.objects.all().order_by('-created')
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
        os_image = ImageDiff.objects.select_related("img_a", "img_b").order_by('-created')
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
            {"label": i[1], "value": i[0]} for i in ImageDiffPKG.TYPE_CHOICES
        ]
        return Response(data=format_resp(data=pkgType), status=status.HTTP_200_OK)


class ImportImageView(APIView):
    """
    Summary:
        import and diff image
    """

    def post(self, request, *args, **kwargs):
        data = request.data
        req_user = request.user
        if isinstance(req_user, AnonymousUser):
            return Response(data=format_resp(code=20001, msg='User not logged in'),
                            status=status.HTTP_401_UNAUTHORIZED)
        img_a = self.judge_import(img=data.get('imgA'))
        img_b = self.judge_import(img=data.get('imgB'))
        job = JenkinsWrapper(server_name='cje_jenkins')
        job.trigger_job(name='image-inspector', group='OpenIKT', data={'img_a': img_a, 'img_b': img_b})
        send_email(
            msg=f'The Openikt image inspector: Image A: {img_a}, Image B: {img_b} job trigger successfully:<br>'
                f'{job.job_url_base}',
            user_email=req_user.email
        )
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


class ImageUrlVerify(APIView):
    """
    Summary:
        Check if Content-Type is a valid image type
    """

    def get(self, request, *args, **kwargs):
        url = request.query_params.get('url')

        if not url:
            return JsonResponse({'valid': False, 'error': 'No URL provided'}, status=400)

        try:
            response = requests.head(url)
            content_type = response.headers.get('Content-Type', '')

            valid_types = ['application/x-iso9660-image', 'application/octet-stream',
                           'application/x-diskimage', 'application/x-raw-disk-image']

            is_valid = any(content_type.startswith(valid) for valid in valid_types)
            return JsonResponse({'valid': is_valid})

        except requests.RequestException as e:
            return JsonResponse({'valid': False, 'error': str(e)}, status=200)


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
            query = query & Q(pkgtype__in=pkg_t)
        image_diff_pag = ImageDiffPKG.objects.filter(query).order_by('pkgtype', 'pkg_a__name', 'pkg_b__name')
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


class JudgeImageDiff(APIView):
    """
    Summary:
        judge image diff exist
    """

    def get(self, request, *args, **kwargs):
        img_a = request.query_params.get('imgA')
        img_b = request.query_params.get('imgB')
        is_exist = ImageDiff.objects.filter(img_a__name=img_a, img_b__name=img_b)
        if is_exist:
            return Response({'is_exist': True, 'id': is_exist.first().id}, status=status.HTTP_200_OK)
        return Response({'is_exist': False}, status=status.HTTP_200_OK)