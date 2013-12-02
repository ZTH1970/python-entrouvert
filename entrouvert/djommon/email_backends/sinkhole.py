from django.conf import settings

from django.core.mail.backends.smtp import EmailBackend as SmtpEmailBackend
from django.core.mail.message import sanitize_address
from django.utils.encoding import force_bytes

class EmailBackend(SmtpEmailBackend):
    def _send(self, email_message):
        """A helper method that does the actual sending."""
        if not email_message.recipients():
            return False
        from_email = sanitize_address(email_message.from_email,
                email_message.encoding)
        recipients = [ settings.EMAIL_SINK_RECIPIENT ]
        message = email_message.message()
        charset = message.get_charset().get_output_charset() if message.get_charset() else 'utf-8'
        try:
            self.connection.sendmail(from_email, recipients,
                    force_bytes(message.as_string(), charset))
        except:
            if not self.fail_silently:
                raise
            return False
        return True

