# app_name/backends/email_backend.py
import ssl
from django.core.mail.backends.smtp import EmailBackend as SmtpBackend
from django.utils.functional import cached_property

class UnverifiedEmailBackend(SmtpBackend):
    @cached_property
    def ssl_context(self):
        # Create a default context but explicitly disable verification
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context
