from . import views
from django.urls import path

urlpatterns = [
    # Authentication endpoints
    path("signup/", views.RegistrationView.as_view()),
    path("signin/", views.SigninAPIView.as_view()),
    path("forgot-password/", views.ForgotPasswordView.as_view(), name="forgot-password"),
    path("verify-otp/", views.VerifyOTPView.as_view(), name="verify-otp"),
    path("reset-password/", views.ResetPasswordView.as_view(), name="reset-password"),
    
    
]