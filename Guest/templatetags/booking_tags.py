from django import template

register = template.Library()

@register.filter
def is_owner(booking, user):
    """Check if user is the owner of the booked property"""
    return booking.can_manage(user)