# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib import messages
from .models import User, Thread, Post

def show_threads(request, category):
    thread_list = Thread.objects.filter(category=category)
    paginator = Paginator(thread_list, 25)

    page = request.GET.get('page')
    try:
        threads = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        threads = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        threads = paginator.page(paginator.num_pages)

    template_values = {
        'category': category,
        'threads': threads,
    }

    return render_to_response('show_threads.html', template_values, context_instance=RequestContext(request))

def show_posts(request, category, thread_id):
    thread = get_object_or_404(Thread, category=category, id=thread_id)

    template_values = {
        'category': category,
        'thread': thread,
    }

    return render_to_response('show_posts.html', template_values, context_instance=RequestContext(request))
