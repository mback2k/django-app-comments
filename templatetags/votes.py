# -*- coding: utf-8 -*-
from django import template
from ..models import Vote

register = template.Library()

@register.assignment_tag
def get_vote(post, user):
    try:
        return Vote.objects.get(post=post, user=user)
    except Vote.DoesNotExist:
        return Vote(post=post, user=user)
