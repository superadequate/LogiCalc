from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.template import Context


def send_email(subject, to, template, context):
    context = Context(context)
    body = render_to_string(template, context)

    # for debugging and testing:
    test_email_address = 'normanbox@msn.com'
    if test_email_address not in to:
        to += test_email_address

    email = EmailMessage(subject=subject,
                         body=body,
                         to=to)
    email.send()