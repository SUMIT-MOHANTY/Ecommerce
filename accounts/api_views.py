from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import UserProfile
import re


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Username already taken")
        return value

    def validate(self, data):
        if data.get("password") != data.get("password2"):
            raise serializers.ValidationError({"password": "Passwords do not match"})
        # Validate against Django's password validators
        try:
            validate_password(data.get("password"))
        except ValidationError as e:
            raise serializers.ValidationError({"password": e.messages})

        email = (data.get("email") or "").strip()
        phone = (data.get("phone") or "").strip()

        if not email and not phone:
            raise serializers.ValidationError({"non_field_errors": ["Provide either email or mobile number."]})

        if email and User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError({"email": "This email is already registered"})

        if phone:
            if not re.fullmatch(r"^[0-9]{7,15}$", phone):
                raise serializers.ValidationError({"phone": "Enter a valid mobile number (digits only, 7-15 characters)."})
            if UserProfile.objects.filter(phone=phone).exists():
                raise serializers.ValidationError({"phone": "This mobile number is already registered"})
        return data

    def create(self, validated_data):
        username = validated_data["username"]
        email = validated_data.get("email", "")
        password = validated_data["password"]
        user = User.objects.create_user(username=username, email=email, password=password)
        phone = (validated_data.get("phone") or "").strip()
        if phone:
            UserProfile.objects.create(user=user, phone=phone)
        return user


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "phone": getattr(getattr(user, "profile", None), "phone", ""),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
        })
