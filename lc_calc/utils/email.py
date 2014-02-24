from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.template import Context


def send_email(subject, to, template, context):
    context = Context(context)
    body = render_to_string(template, context)
    email = EmailMessage(subject=subject,
                         body=body,
                         to=to)
    email.send()