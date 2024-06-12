"""login api view page"""

import json
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View


@method_decorator(csrf_exempt, name="dispatch")
class RegisterView(View):
    """user register view"""

    def post(self, request):
        """register api"""
        data = json.loads(request.body)
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        # check user exists
        if User.objects.filter(username=username).exists():
            return JsonResponse({"error": "Username already exists"}, status=400)

        # create new user
        user = User.objects.create_user(
            username=username, email=email, password=password
        )
        user.save()

        return JsonResponse({"message": "User registered successfully"}, status=201)


@method_decorator(csrf_exempt, name="dispatch")
class LoginView(View):
    """user login view"""

    def post(self, request):
        """login api"""
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return JsonResponse({"message": "Login successful"}, status=200)
        else:
            return JsonResponse({"error": "Invalid credentials"}, status=400)


def logoutView(request):
    """user logout view"""
    logout(request)
    return JsonResponse({"message": "Logout successful"}, status=200)
