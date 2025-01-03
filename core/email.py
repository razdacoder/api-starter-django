from django.core import mail
from django.views.generic.base import ContextMixin
from django.template.context import make_context
from django.template.loader import get_template
from django.conf import settings as django_settings
from django.contrib.sites.shortcuts import get_current_site

class BaseEmailMessage(mail.EmailMultiAlternatives, ContextMixin):
    _node_map = {
        "subject": "subject",
        "text_body": "body",
        "html_body": "html",
    }
    template_name = None

    def __init__(self,  context=None, template_name=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
       
        self.context = {} if context is None else context
        self.html = None

        if template_name is not None:
            self.template_name = template_name

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        context = dict(ctx, **self.context)
       
     
        domain = context.get("domain") or getattr(django_settings, "DOMAIN", "")
        protocol = context.get("protocol") or "http"
        site_name = context.get("site_name") or getattr(
            django_settings, "SITE_NAME", ""
        )
        user = context.get("user")

        context.update(
            {
                "domain": domain,
                "protocol": protocol,
                "site_name": site_name,
                "user": user,
            }
        )
        return context

    def render(self):
        context = make_context(self.get_context_data())
        template = get_template(self.template_name)
        with context.bind_template(template.template):
            for node in template.template.nodelist:
                self._process_node(node, context)
        self._attach_body()

    # custom interface incompatible with django, `to` is a required param
    def send(self, to, fail_silently=False, **kwargs):
        self.render()

        self.to = to
        self.cc = kwargs.pop("cc", [])
        self.bcc = kwargs.pop("bcc", [])
        self.reply_to = kwargs.pop("reply_to", [])
        self.from_email = kwargs.pop("from_email", django_settings.DEFAULT_FROM_EMAIL)
        self.request = None
        super().send(fail_silently=fail_silently)

    def _process_node(self, node, context):
        attr = self._node_map.get(getattr(node, "name", ""))
        if attr is not None:
            setattr(self, attr, node.render(context).strip())

    def _attach_body(self):
        if self.body and self.html:
            self.attach_alternative(self.html, "text/html")
        elif self.html:
            self.body = self.html
            self.content_subtype = "html"

