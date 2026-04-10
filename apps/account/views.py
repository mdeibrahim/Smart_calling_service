from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from .models import PasswordResetOTP, User
from .serializers import (
    UserSerializer,
    ForgotPasswordSerializer, 
    ResetPasswordSerializer, VerifyOTPSerializer
)


class RegistrationView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "success": True,
                    "message": "User registered successfully",
                    "user": UserSerializer(user).data,
                    "status_code": status.HTTP_201_CREATED,
                },
                status=status.HTTP_201_CREATED,
            )
        raise ValidationError(serializer.errors)
    

class SigninAPIView(APIView):

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        user = authenticate(request, email=email, password=password)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "User signed in successfully",
                    "user": UserSerializer(user).data,
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                status=status.HTTP_200_OK,
            )
        raise ValidationError("Invalid credentials")



class ForgotPasswordView(APIView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            user = User.objects.get(email=email)
            otp_code = PasswordResetOTP.generate_otp()
            PasswordResetOTP.objects.create(user=user, otp=otp_code)

            # Send OTP via email (and show in response for testing)
            send_mail(
                subject="Your Password Reset OTP",
                message=f"Hello {user.name or user.email},\nYour OTP for password reset is: {otp_code}\nValid for 5 minutes.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )

            return Response(
                {
                    "success": True,
                    "message": "OTP sent to your email",
                    "otp": otp_code,  # ✅ For development/testing
                    "status_code": status.HTTP_200_OK,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"success": False, "errors": serializer.errors, "status_code": status.HTTP_400_BAD_REQUEST},
            status=status.HTTP_400_BAD_REQUEST,
        )


# 2️⃣ Verify OTP
class VerifyOTPView(APIView):
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            otp = serializer.validated_data["otp"]

            try:
                user = User.objects.get(email=email)
                otp_entry = PasswordResetOTP.objects.filter(user=user, otp=otp, is_used=False).last()

                if not otp_entry:
                    return Response(
                        {"success": False, "message": "Invalid OTP", "status_code": status.HTTP_400_BAD_REQUEST},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if not otp_entry.is_valid():
                    return Response(
                        {"success": False, "message": "OTP expired", "status_code": status.HTTP_400_BAD_REQUEST},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                otp_entry.is_verified = True
                otp_entry.save()

                return Response(
                    {"success": True, "message": "OTP verified successfully", "status_code": status.HTTP_200_OK},
                    status=status.HTTP_200_OK,
                )

            except User.DoesNotExist:
                return Response(
                    {"success": False, "message": "User not found", "status_code": status.HTTP_404_NOT_FOUND},
                    status=status.HTTP_404_NOT_FOUND,
                )

        return Response(
            {"success": False, "errors": serializer.errors, "status_code": status.HTTP_400_BAD_REQUEST},
            status=status.HTTP_400_BAD_REQUEST,
        )


# 3️⃣ Reset Password (after successful OTP verification)
class ResetPasswordView(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            new_password = serializer.validated_data["new_password"]

            try:
                user = User.objects.get(email=email)
                otp_entry = PasswordResetOTP.objects.filter(user=user, is_verified=True, is_used=False).last()

                if not otp_entry:
                    return Response(
                        {"success": False, "message": "OTP not verified", "status_code": status.HTTP_400_BAD_REQUEST},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                user.set_password(new_password)
                user.save()
                otp_entry.is_used = True
                otp_entry.save()

                return Response(
                    {"success": True, "message": "Password reset successfully", "status_code": status.HTTP_200_OK},
                    status=status.HTTP_200_OK,
                )

            except User.DoesNotExist:
                return Response(
                    {"success": False, "message": "User not found", "status_code": status.HTTP_404_NOT_FOUND},
                    status=status.HTTP_404_NOT_FOUND,
                )

        return Response(
            {"success": False, "errors": serializer.errors, "status_code": status.HTTP_400_BAD_REQUEST},
            status=status.HTTP_400_BAD_REQUEST,
        )