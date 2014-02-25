from django import template

register = template.Library()


def percentage(value):
    try:
        return '{0:.2%}'.format(value)
    except ValueError:
        return None

register.filter('percentage', percentage)