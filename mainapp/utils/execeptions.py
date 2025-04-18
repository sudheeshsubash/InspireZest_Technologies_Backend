from rest_framework.views import exception_handler
from rest_framework.exceptions import *
from mainapp.utils.responses import CustomResponse
from rest_framework import status

def custom_exception_handler(exc, context):
    # Call the default exception handler first
    response = exception_handler(exc, context)

    if isinstance(exc, AuthenticationFailed):
        # Customize the response data
        response = CustomResponse(message='Invalid or expired token',status=status.HTTP_401_UNAUTHORIZED)

        # Delete the 'jwt' cookie from the response
        response.delete_cookie('jwt')

    return response
