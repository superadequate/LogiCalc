from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.template import Context


def send_email(subject, to, template, context):
    context = Context(context)
    body = render_to_string(template, context)

    # for debugging and testing:
    test_email_address = 'normanbox@msn.com'

    email = EmailMessage(subject=subject,
                         body=body,
                         to=to,
                         bcc=[test_email_address])
    email.send()