from django.apps import apps
from django.conf import settings as django_settings
from django.test.signals import setting_changed
from django.utils.functional import LazyObject
from django.utils.module_loading import import_string

USERS_SETTINGS_NAMESPACE = "USERS_AUTH"

auth_module, user_model = django_settings.AUTH_USER_MODEL.rsplit(".", 1)

User = apps.get_model(auth_module, user_model)


class ObjDict(dict):
    def __getattribute__(self, item):
        try:
            val = self[item]
            if isinstance(val, str):
                val = import_string(val)
            elif isinstance(val, (list, tuple)):
                val = [import_string(v) if isinstance(v, str) else v for v in val]
            self[item] = val
        except KeyError:
            val = super().__getattribute__(item)

        return val


default_settings = {
    "USER_ID_FIELD": User._meta.pk.name,
    "LOGIN_FIELD": User.USERNAME_FIELD,
    "SEND_ACTIVATION_EMAIL": True,
    "SEND_CONFIRMATION_EMAIL": True,
    "USER_CREATE_PASSWORD_RETYPE": True,
    "SET_PASSWORD_RETYPE": True,
    "PASSWORD_RESET_CONFIRM_RETYPE": True,
    "PASSWORD_RESET_SHOW_EMAIL_NOT_FOUND": False,
    "PASSWORD_CHANGED_EMAIL_CONFIRMATION": False,
    "TOKEN_MODEL": "rest_framework.authtoken.models.Token",
    "SERIALIZERS": ObjDict(
        {
            "activation": "users.serializers.ActivationSerializer",
            "password_reset": "users.serializers.SendEmailResetSerializer",
            "password_reset_confirm": "users.serializers.PasswordResetConfirmSerializer",
            "password_reset_confirm_retype": "users.serializers.PasswordResetConfirmRetypeSerializer",
            "set_password": "users.serializers.SetPasswordSerializer",
            "set_password_retype": "users.serializers.SetPasswordRetypeSerializer",
            "user_create": "users.serializers.UserCreateSerializer",
            "user_create_password_retype": "users.serializers.UserCreatePasswordRetypeSerializer",
            "user_delete": "users.serializers.UserDeleteSerializer",
            "user": "users.serializers.UserSerializer",
            "current_user": "users.serializers.UserSerializer",
            "token": "users.serializers.TokenSerializer",
            "token_create": "users.serializers.TokenCreateSerializer",
        }
    ),
    "EMAIL": ObjDict(
        {
            "activation": "users.email.ActivationEmail",
            "confirmation": "users.email.ConfirmationEmail",
            "password_reset": "users.email.PasswordResetEmail",
            "password_changed_confirmation": "users.email.PasswordChangedConfirmationEmail",
           
        }
    ),
    "EMAIL_FRONTEND_DOMAIN": "http://localhost:3000",
    "EMAIL_FRONTEND_PROTOCOL": "http",
    "EMAIL_FRONTEND_SITE_NAME": "Django API Starter",
    "CONSTANTS": ObjDict({"messages": "users.constants.Messages"}),
    "LOGOUT_ON_PASSWORD_CHANGE": True,
    "CREATE_SESSION_ON_LOGIN": False,
    # "SOCIAL_AUTH_TOKEN_STRATEGY": "users.social.token.jwt.TokenStrategy",
    # "SOCIAL_AUTH_ALLOWED_REDIRECT_URIS": [],
    "HIDE_USERS": True,
    "PERMISSIONS": ObjDict(
        {
            "activation": ["rest_framework.permissions.AllowAny"],
            "password_reset": ["rest_framework.permissions.AllowAny"],
            "password_reset_confirm": ["rest_framework.permissions.AllowAny"],
            "set_password": ["users.permissions.CurrentUserOrAdmin"],
            "username_reset": ["rest_framework.permissions.AllowAny"],
            "username_reset_confirm": ["rest_framework.permissions.AllowAny"],
            "set_username": ["users.permissions.CurrentUserOrAdmin"],
            "user_create": ["rest_framework.permissions.AllowAny"],
            "user_delete": ["users.permissions.CurrentUserOrAdmin"],
            "user": ["users.permissions.CurrentUserOrAdmin"],
            "user_list": ["users.permissions.CurrentUserOrAdmin"],
            "token_create": ["rest_framework.permissions.AllowAny"],
            "token_destroy": ["rest_framework.permissions.IsAuthenticated"],
        }
    ),
    # "WEBAUTHN": ObjDict(
    #     {
    #         "RP_NAME": "localhost",
    #         "RP_ID": "localhost",
    #         "ORIGIN": "http://localhost:8000",
    #         "CHALLENGE_LENGTH": 32,
    #         "UKEY_LENGTH": 20,
    #         "SIGNUP_SERIALIZER": "users.webauthn.serializers.WebauthnCreateUserSerializer",
    #         "LOGIN_SERIALIZER": "users.webauthn.serializers.WebauthnLoginSerializer",
    #     }
    # ),
}

SETTINGS_TO_IMPORT = []
# SOCIAL_AUTH_TOKEN_STRATEGY, TOKEN_MODEL


class Settings:
    def __init__(self, default_settings, explicit_overriden_settings: dict = None):
        if explicit_overriden_settings is None:
            explicit_overriden_settings = {}

        overriden_settings = (
            getattr(django_settings, USERS_SETTINGS_NAMESPACE, {})
            or explicit_overriden_settings
        )

        self._load_default_settings()
        self._override_settings(overriden_settings)
        self._init_settings_to_import()

    def _load_default_settings(self):
        for setting_name, setting_value in default_settings.items():
            if setting_name.isupper():
                setattr(self, setting_name, setting_value)

    def _override_settings(self, overriden_settings: dict):
        for setting_name, setting_value in overriden_settings.items():
            value = setting_value
            if isinstance(setting_value, dict):
                value = getattr(self, setting_name, {})
                value.update(ObjDict(setting_value))
            setattr(self, setting_name, value)

    def _init_settings_to_import(self):
        for setting_name in SETTINGS_TO_IMPORT:
            value = getattr(self, setting_name)
            if isinstance(value, str):
                setattr(self, setting_name, import_string(value))


class LazySettings(LazyObject):
    def _setup(self, explicit_overriden_settings=None):
        self._wrapped = Settings(default_settings, explicit_overriden_settings)


settings = LazySettings()


def reload_users_settings(*args, **kwargs):
    global settings
    setting, value = kwargs["setting"], kwargs["value"]
    if setting == USERS_SETTINGS_NAMESPACE:
        settings._setup(explicit_overriden_settings=value)


setting_changed.connect(reload_users_settings)