from django.urls import path
from application import views

urlpatterns = [
    path('registration', views.RegistrationApiView.as_view()),
    path('otpvalidation', views.OTPVerificationApiView.as_view()),
    path('login', views.LoginApiView.as_view()),
]
