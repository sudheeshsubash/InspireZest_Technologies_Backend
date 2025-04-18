from django.db import transaction, DatabaseError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail
from django.conf import settings

from .serializers import UserSerializer, LeavesSerializer, TaskSerializer
from mainapp.models import User, Task, Leaves

import random
import asyncio

from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken



class RegistrationApiView(APIView):
    """
    API endpoint to register a new user.
    - Accepts: username, email, and password.
    - Generates an OTP and saves the user in an unverified state.
    - Sends the OTP to the user's email for verification.
    """

    @transaction.atomic
    def post(self, request):
        try:
            # Initialize serializer with input data
            serializer = UserSerializer(data=request.data, fields=['username', 'email', 'password'])

            if serializer.is_valid():
                # Generate a secure 6-digit OTP
                otp_number = random.randint(111111, 999999)

                send_mail(
                    subject="Registration OTP",
                    message=f"Usermanagement system Registration OTP: {otp_number}. Don't share this with anyone.",
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[serializer.validated_data['email']],
                    fail_silently=False,
                )

                # Save user with OTP and mark as unverified
                serializer.save(OTP=otp_number, is_verified=False, role='manager')

                return Response(
                    {"message": _("User registered successfully. OTP has been sent to your email.")},
                    status=status.HTTP_201_CREATED
                )

            return Response(
                {
                    "message": _("Invalid registration credentials."),
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except DatabaseError as db_error:
            return Response(
                {"message": _("Database error occurred."), "error": str(db_error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        except Exception as error:
            return Response(
                {"message": _("An unexpected error occurred during registration."), "error": str(error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OTPVerificationApiView(APIView):
    """
    API endpoint for verifying OTP.
    - Accepts: username and OTP.
    - Marks the user as verified if OTP matches.
    """

    def post(self, request):
        try:
            username = request.data.get('username')
            otp = request.data.get('OTP')
            print(username, otp)

            if not username or not otp:
                return Response(
                    {"message": _("Username or OTP is missing.")},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Retrieve the user by username
            user = User.objects.get(username=username)

            # Verify the OTP
            if str(user.OTP) == str(otp):
                user.is_verified = True
                user.save()
                return Response(
                    {"message": _("OTP verification successful.")},
                    status=status.HTTP_200_OK
                )

            return Response(
                {"message": _("Invalid OTP provided.")},
                status=status.HTTP_400_BAD_REQUEST
            )

        except User.DoesNotExist:
            return Response(
                {"message": _("User with this username does not exist.")},
                status=status.HTTP_404_NOT_FOUND
            )

        except DatabaseError as db_error:
            return Response(
                {"message": _("Database error occurred."), "error": str(db_error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        except Exception as error:
            return Response(
                {"message": _("An unexpected error occurred during OTP verification."), "error": str(error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class LoginApiView(APIView):
    """
    API endpoint to authenticate a user with either username or email and password.
    Only users who are verified (is_verified=True) can log in.
    """

    def post(self, request):
        try:
            identifier = request.data.get("username")
            password = request.data.get("password")

            if not identifier or not password:
                return Response(
                    {"message": _("Username and password are required.")},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Try to fetch the user by username or email
            try:
                user = User.objects.get(username=identifier)
            except User.DoesNotExist:
                return Response(
                    {"message": _("User not found.")},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check if the user is verified
            if not user.is_verified:
                return Response(
                    {"message": _("Your account is not verified. Please verify your email before logging in.")},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Authenticate the user using Django's authentication system
            user = authenticate(username=user.username, password=password)

            if user is not None:
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                return Response(
                    {
                        "message": _("Login successful."),
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                        "user": {
                            "id": user.id,
                            "username": user.username,
                            "role": user.role,
                        }
                    },
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"message": _("Invalid credentials.")},
                    status=status.HTTP_401_UNAUTHORIZED
                )

        except DatabaseError as db_error:
            return Response(
                {"message": _("Database error occurred."), "error": str(db_error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        except Exception as error:
            return Response(
                {"message": _("An unexpected error occurred."), "error": str(error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class DashboardApiView(APIView):
    def get(self, request):
        pass


class UserApiView(APIView):
    def get(self, request):
        pass
    
    def post(self, request):
        pass


class SingleUserApiView(APIView):
    def get(self, request):
        pass
    
    def patch(self, request):
        pass
    
    def delete(self, request):
        pass


class TaskApiView(APIView):
    def get(self, request):
        pass
    
    def post(self, request):
        pass
    

class SingleTaskApiView(APIView):
    def get(self, request):
        pass
    
    def patch(self, request):
        pass
    
    def delete(self, request):
        pass


class LeaveApiView(APIView):
    def get(self, request):
        pass
    
    def post(self, request):
        pass


class SingleLeaveApiView(APIView):
    def get(self, request):
        pass
    
    def patch(self, request):
        pass
    
    def delete(self, request):
        pass

