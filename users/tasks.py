from celery import shared_task
from .config import settings

@shared_task
def send_activation_email(context, to):
    email = settings.EMAIL.activation(context=context)
    email.send(to=to)

@shared_task
def send_confirmation_email(context, to):
    settings.EMAIL.confirmation(context).send(to)


@shared_task
def send_password_reset_email(context, to):
    settings.EMAIL.password_reset(context).send(to)

@shared_task
def send_password_changed_confirmation_email(context, to):
    settings.EMAIL.password_changed_confirmation(context).send(to)