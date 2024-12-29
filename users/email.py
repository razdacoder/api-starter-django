from django.contrib.sites.shortcuts import get_current_site
from . import utils
from django.conf import settings as django_settings
from .config import settings
from core.email import BaseEmailMessage
from core.utils import generate_otp, OTPPurposeEnum




class BaseUserEmail(BaseEmailMessage):
    def get_context_data(self):
        context = super().get_context_data()
        overridable = {
            "protocol": settings.EMAIL_FRONTEND_PROTOCOL,
            "domain": settings.EMAIL_FRONTEND_DOMAIN,
            "site_name": settings.EMAIL_FRONTEND_SITE_NAME,
        }
        for context_key, context_value in overridable.items():
            if context_value:
                context.update({context_key: context_value})
        context.pop("view", None)
        return context


class ActivationEmail(BaseUserEmail):
    template_name = "email/activation.html"

    def get_context_data(self):
        context = super().get_context_data()

        user = context.get("user")
        otp = generate_otp(user, OTPPurposeEnum.ACTIVATION)
        context["otp"] = otp
        context["otp_validity"] = 10
        return context


class ConfirmationEmail(BaseUserEmail):
    template_name = "email/confirmation.html"


class PasswordResetEmail(BaseUserEmail):
    template_name = "email/password_reset.html"

    def get_context_data(self):
        context = super().get_context_data()

        user = context.get("user")
        otp = generate_otp(user, OTPPurposeEnum.PASSWORD_RESET)
        context["otp"] = otp
        context["otp_validity"] = 10
        return context


class PasswordChangedConfirmationEmail(BaseUserEmail):
    template_name = "email/password_changed_confirmation.html"


# class UsernameChangedConfirmationEmail(BaseDjoserEmail):
#     template_name = "email/username_changed_confirmation.html"


# class UsernameResetEmail(BaseDjoserEmail):
    template_name = "email/username_reset.html"

    def get_context_data(self):
        context = super().get_context_data()

        user = context.get("user")
        context["uid"] = utils.encode_uid(user.pk)
        context["token"] = default_token_generator.make_token(user)
        context["url"] = settings.USERNAME_RESET_CONFIRM_URL.format(**context)
        return context