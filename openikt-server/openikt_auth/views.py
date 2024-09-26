"""login api view page"""

import json
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from app_diff.methods import format_resp


@method_decorator(csrf_exempt, name="dispatch")
class RegisterView(APIView):
    """user register view"""

    def post(self, request):
        """register api"""
        data = json.loads(request.body)
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        # check user exists
        if User.objects.filter(username=username).exists():
            return Response(data=format_resp(data={"error": "Username already exists"}), status=status.HTTP_200_OK)

        # create new user
        user = User.objects.create_user(
            username=username, email=email, password=password
        )
        user.save()

        return Response(data=format_resp(data={'msg':'register successfully'}), status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name="dispatch")
class LoginView(APIView):
    """user login view"""

    def post(self, request):
        """login api"""
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            res =  Response(data=format_resp(data={'msg':'login successfully'}), status=status.HTTP_200_OK)
            res.set_cookie(key='username', value=username.capitalize(), max_age=1209600)
            return res
        else:
            return Response(data=format_resp(data={'error':'login failed'}), status=status.HTTP_200_OK)

class LogoutView(APIView):
    def get(self, request):
        """user logout view"""
        logout(request)
        res = Response(data=format_resp(data={'msg':'logout successfully'}), status=status.HTTP_200_OK)
        res.delete_cookie(key='username')
        return res
