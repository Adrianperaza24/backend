from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import RetrieveUpdateAPIView

from .models import User, PrivacyConsent
from .permissions import IsHRorMaster
from .serializers import (
    UserCreateSerializer,
    UserMeSerializer,
    PrivacyConsentSerializer,
)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [IsHRorMaster]


class ProtectedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"status": "Request was permitted"})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = UserMeSerializer(request.user).data
        return Response(data)


class PrivacyConsentView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PrivacyConsentSerializer

    def get_object(self):
        obj, _ = PrivacyConsent.objects.get_or_create(user=self.request.user)
        return obj