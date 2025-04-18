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
    """
    Optimized API endpoint to provide dashboard metrics:
    - Total tasks
    - Total leaves
    - Salary calculation (adjusted based on leaves)
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user

            # Optimize queries
            total_tasks = Task.objects.filter(user=user).count()
            leaves_qs = Leaves.objects.filter(user=user)

            total_leaves = leaves_qs.count()

            # Compute total leave days via annotation (only works if DB is PostgreSQL or supports date difference)
            leave_days = sum(
                (leave.end_date - leave.start_date).days + 1
                for leave in leaves_qs.only('start_date', 'end_date')
            )

            # Calculate salary
            daily_salary = user.salary / 30
            deducted_salary = daily_salary * leave_days
            net_salary = max(0, user.salary - deducted_salary)

            return Response({
                "message": _("Dashboard data fetched successfully."),
                "data": {
                    "total_tasks": total_tasks,
                    "total_leaves": total_leaves,
                    "leave_days": leave_days,
                    "monthly_salary": round(user.salary, 2),
                    "deducted_salary": round(deducted_salary, 2),
                    "net_salary": round(net_salary, 2),
                }
            }, status=status.HTTP_200_OK)

        except Exception as error:
            return Response({
                "message": _("An unexpected error occurred while loading dashboard."),
                "error": str(error)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserApiView(APIView):
    """
    API view to handle listing and creating employee users.
    """
    permission_classes = [IsAuthenticated]
    

    def get(self, request):
        """
        Retrieve a list of all employee users.
        """
        try:
            users = User.objects.filter(role='employee')
            serializer = UserSerializer(users, many=True, fields=['username', 'email', 'salary'])

            return Response({
                "message": _("User data fetched successfully."),
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except DatabaseError as db_error:
            return Response({
                "message": _("Database error occurred."),
                "error": str(db_error)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as error:
            return Response({
                "message": _("An unexpected error occurred."),
                "error": str(error)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @transaction.atomic
    def post(self, request):
        """
        Create a new employee user account.
        """
        try:
            serializer = UserSerializer(data=request.data, fields=['username', 'email', 'salary', 'password'])

            if serializer.is_valid():
                serializer.save(is_verified=True)
                return Response({
                    "message": _("New employee account created successfully.")
                }, status=status.HTTP_201_CREATED)

            return Response({
                "message": _("Employee account creation failed."),
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except DatabaseError as db_error:
            return Response({
                "message": _("Database error occurred."),
                "error": str(db_error)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as error:
            return Response({
                "message": _("An unexpected error occurred."),
                "error": str(error)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SingleUserApiView(APIView):
    """
    API view to handle retrieving, updating, and deleting a single employee user.
    """
    permission_classes = [IsAuthenticated]
    

    def get(self, request, id):
        """
        Retrieve details of a specific employee user.
        """
        try:
            user = User.objects.get(id=id)
            serializer = UserSerializer(user, fields=['username', 'email', 'salary'])

            return Response({
                "message": _(f"User data fetched successfully for ID {id}."),
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({
                "message": _(f"No user found with ID {id}.")
            }, status=status.HTTP_404_NOT_FOUND)

        except DatabaseError as db_error:
            return Response({
                "message": _("Database error occurred."),
                "error": str(db_error)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as error:
            return Response({
                "message": _("An unexpected error occurred."),
                "error": str(error)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @transaction.atomic
    def patch(self, request, id):
        """
        Partially update a specific employee user.
        """
        try:
            user = User.objects.get(id=id)
            serializer = UserSerializer(user, data=request.data, fields=['username', 'email', 'salary'], partial=True)

            if serializer.is_valid():
                serializer.save()
                return Response({
                    "message": _(f"User data updated successfully for ID {id}."),
                    "data": serializer.data
                }, status=status.HTTP_200_OK)

            return Response({
                "message": _("User update failed."),
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            return Response({
                "message": _(f"No user found with ID {id}.")
            }, status=status.HTTP_404_NOT_FOUND)

        except DatabaseError as db_error:
            return Response({
                "message": _("Database error occurred."),
                "error": str(db_error)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as error:
            return Response({
                "message": _("An unexpected error occurred."),
                "error": str(error)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @transaction.atomic
    def delete(self, request, id):
        """
        Delete a specific employee user.
        """
        try:
            user = User.objects.get(id=id)
            user.delete()

            return Response({
                "message": _(f"User with ID {id} has been deleted.")
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({
                "message": _(f"No user found with ID {id}.")
            }, status=status.HTTP_404_NOT_FOUND)

        except DatabaseError as db_error:
            return Response({
                "message": _("Database error occurred."),
                "error": str(db_error)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as error:
            return Response({
                "message": _("An unexpected error occurred."),
                "error": str(error)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class TaskApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            if user.role == 'manager': # if manager return all task, if employee return there tasks
                tasks = Task.objects.all()
            else:
                tasks = Task.objects.filter(assign_to=user)
            serializer = TaskSerializer(tasks, many=True)
            return Response({
                "message": _("Tasks fetched successfully."),
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as error:
            return Response({
                "message": _("An error occurred while fetching tasks."),
                "error": str(error)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @transaction.atomic
    def post(self, request):
        try:
            serializer = TaskSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "message": _("Task created successfully."),
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)
            return Response({
                "message": _("Task creation failed."),
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response({
                "message": _("An error occurred while creating the task."),
                "error": str(error)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    
class SingleTaskApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            user = request.user
            if user.role == 'manager': # manager can access all task
                task = Task.objects.get(id=id)
            else:
                task = Task.objects.get(id=id, assign_to=user) # employess can access there assigned task
            serializer = TaskSerializer(task)
            return Response({
                "message": _("Task retrieved successfully."),
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Task.DoesNotExist:
            return Response({
                "message": _("Task not found.")
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as error:
            return Response({
                "message": _("An error occurred while retrieving the task."),
                "error": str(error)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @transaction.atomic
    def patch(self, request, id):
        try:
            user = request.user
            if user.role == 'manager': # manager can access all task
                task = Task.objects.get(id=id)
            else:
                task = Task.objects.get(id=id, assign_to=user) # employess can access there assigned task
            serializer = TaskSerializer(task, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "message": _("Task updated successfully."),
                    "data": serializer.data
                }, status=status.HTTP_200_OK)
            return Response({
                "message": _("Task update failed."),
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Task.DoesNotExist:
            return Response({
                "message": _("Task not found.")
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as error:
            return Response({
                "message": _("An error occurred while updating the task."),
                "error": str(error)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @transaction.atomic
    def delete(self, request, id):
        try:
            user = request.user
            if user.role == 'manager': # manager can access all task
                task = Task.objects.get(id=id)
                task.delete()
                return Response({
                    "message": _("Task deleted successfully.")
                }, status=status.HTTP_200_OK)
            return Response(
                {
                    "message":_("employee can't delete task")
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Task.DoesNotExist:
            return Response({
                "message": _("Task not found.")
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as error:
            return Response({
                "message": _("An error occurred while deleting the task."),
                "error": str(error)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class LeaveApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            if user.role == 'manager': # manager can access all leaves
                leaves = Leaves.objects.all()
            else:
                leaves = Leaves.objects.filter(user=user)
            serializer = LeavesSerializer(leaves, many=True)
            return Response({
                "message": _("Leaves fetched successfully."),
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as error:
            return Response({
                "message": _("An error occurred while fetching leaves."),
                "error": str(error)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @transaction.atomic
    def post(self, request):
        try:
            serializer = LeavesSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "message": _("Leave request created successfully."),
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)
            return Response({
                "message": _("Leave request creation failed."),
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response({
                "message": _("An error occurred while creating leave request."),
                "error": str(error)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SingleLeaveApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            user = request.user
            if user.role == 'manager':
                leave = Leaves.objects.get(id=id)
            else:
                leave = Leaves.objects.get(id=id, user=user)
            serializer = LeavesSerializer(leave)
            return Response({
                "message": _("Leave request retrieved successfully."),
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Leaves.DoesNotExist:
            return Response({
                "message": _("Leave request not found.")
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as error:
            return Response({
                "message": _("An error occurred while retrieving leave request."),
                "error": str(error)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @transaction.atomic
    def patch(self, request, id):
        try:
            user = request.user
            if user.role == 'manager':
                leave = Leaves.objects.get(id=id)
            else:
                leave = Leaves.objects.get(id=id, user=user)
            serializer = LeavesSerializer(leave, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "message": _("Leave request updated successfully."),
                    "data": serializer.data
                }, status=status.HTTP_200_OK)
            return Response({
                "message": _("Leave request update failed."),
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Leaves.DoesNotExist:
            return Response({
                "message": _("Leave request not found.")
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as error:
            return Response({
                "message": _("An error occurred while updating leave request."),
                "error": str(error)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @transaction.atomic
    def delete(self, request, id):
        try:
            leave = Leaves.objects.get(id=id)
            leave.delete()
            return Response({
                "message": _("Leave request deleted successfully.")
            }, status=status.HTTP_200_OK)
        except Leaves.DoesNotExist:
            return Response({
                "message": _("Leave request not found.")
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as error:
            return Response({
                "message": _("An error occurred while deleting leave request."),
                "error": str(error)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
