# from rest_framework.authentication import BaseAuthentication
# from rest_framework import exceptions
# from django.conf import settings
# from jwt import decode as jwt_decode
# from jwt.exceptions import InvalidTokenError
# from rest_framework_simplejwt.tokens import RefreshToken


# class JWTAuthenticationFromCookie(BaseAuthentication):
#     def authenticate(self, request):
#         token = request.COOKIES.get('ACC')

#         if not token:
#             return None  # No token provided

#         try:
#             # Decode the token to get the payload
#             jwt_options = {'verify_exp': True}
#             decoded_data = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"], options=jwt_options)
#             user_id = decoded_data.get('user_id')

#             # Retrieve the user
#             from main.models import BaseUser  # Replace with your actual user model
#             user = BaseUser.objects.get(id=user_id)
#             return (user, None)
#         except InvalidTokenError:
#                 raise exceptions.AuthenticationFailed('Invalid or expired token')

