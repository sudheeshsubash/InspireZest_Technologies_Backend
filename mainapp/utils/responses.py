from rest_framework.response import Response

class CustomResponse(Response):
    def __init__(self, data=None, error=None, message='', status=None, template_name=None, headers=None, exception=False, content_type=None):
        response_data = {
            'message': message,
            'data': data,
            'error': error,
        }
        super(CustomResponse, self).__init__(response_data, status, template_name, headers, exception, content_type)

