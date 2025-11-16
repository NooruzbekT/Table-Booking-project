from rest_framework.throttling import AnonRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """Rate limiting для логина: 5 попыток в час"""
    scope = "login"


class RegisterRateThrottle(AnonRateThrottle):
    """Rate limiting для регистрации: 3 попытки в час"""
    scope = "register"
