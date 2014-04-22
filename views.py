# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib import messages
from .models import User, Thread, Post

def show_threads(request, category):
    template_values = {
        'category': category,
        'threads': Thread.objects.filter(category=category)
    }

    return render_to_response('show_threads.html', template_values, context_instance=RequestContext(request))

def show_posts(request, category, thread_id):
    thread = get_object_or_404(Thread, category=category, id=thread_id)

    template_values = {
        'category': category,
        'thread': thread,
    }

    return render_to_response('show_posts.html', template_values, context_instance=RequestContext(request))
