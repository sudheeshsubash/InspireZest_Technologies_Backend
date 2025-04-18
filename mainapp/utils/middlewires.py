from django.utils.deprecation import MiddlewareMixin
from jwt import decode, ExpiredSignatureError, InvalidTokenError
from django.conf import settings
from datetime import datetime
from django.http import HttpResponse

class JWTAuthCookieMiddleware(MiddlewareMixin):
    def process_request(self, request):
        token = request.COOKIES.get('TA_')  # Replace 'TA_' with your cookie name
        
        if token:
            try:
                # Decode the JWT token
                decoded_token = decode(token, key=settings.JWT_KEY, algorithms=["HS256"])
                expiration_time = datetime.fromtimestamp(decoded_token['exp'])
                
                # Check if the token is expired
                if expiration_time > datetime.now():
                    # If valid, pass it in META
                    request.META['HTTP_AUTHORIZATION'] = f'Bearer {token}'
                else:
                    # Token expired: remove cookie
                    self._delete_cookie(request, 'TA_')
                    self._delete_cookie(request, 'TR_')
            except ExpiredSignatureError:
                # Handle expired token: remove cookie
                self._delete_cookie(request, 'TA_')
                self._delete_cookie(request, 'TR_')
            except InvalidTokenError:
                # Handle invalid token: remove cookie
                self._delete_cookie(request, 'TA_')
                self._delete_cookie(request, 'TR_')
        else:
            print("No token found in cookies.")

    def _delete_cookie(self, request, cookie_name):
        """
        Utility function to delete a cookie by setting it with an expired max_age.
        """
        response = HttpResponse()
        response.delete_cookie(cookie_name)
        request.COOKIES.pop(cookie_name, None)  # Remove from request's cookies
