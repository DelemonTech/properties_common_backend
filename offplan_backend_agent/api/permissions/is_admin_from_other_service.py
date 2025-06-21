from rest_framework.permissions import BasePermission
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


class IsAdminFromAuthService(BasePermission):
    def has_permission(self, request, view):
        try:
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                raise AuthenticationFailed("Missing or invalid Authorization header")

            token = auth_header.split(" ")[1]
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(token)

            role = validated_token.get("role")
            if role != "admin":
                raise AuthenticationFailed("User is not an admin")

            # Optionally attach user info to request
            request.auth_payload = validated_token  # if you want username/id later
            return True

        except Exception as e:
            raise AuthenticationFailed(f"Admin authentication failed: {str(e)}")
