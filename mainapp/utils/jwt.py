from rest_framework_simplejwt.tokens import RefreshToken


def get_tokens_for_user(user):
    token = RefreshToken.for_user(user)
    role = user.role
    token['role'] = role
    return {
        'refresh': str(token),
        'access': str(token.access_token),
    }
