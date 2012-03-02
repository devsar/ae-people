"""
    Stats views
"""
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson
from django.utils.translation import ugettext_lazy as _


from google.appengine.api import taskqueue
from google.appengine.ext.deferred import deferred

from country.models import Country, COUNTRIES_CODE
from users.models import Developer
from country.models import Country
from stats.models import DeveloperStats, TagStats


def update_stats(request):
    """
        Update stats trigger view
    """
    
    DeveloperStats.update()
    
    return HttpResponse("")


def view_stats(request):
    """
        Show AppEngine general stats
    """
    countries = Country.all().filter("total >", 0).order("-total").fetch(250)
    
    #Get last stats
    stats = DeveloperStats.all().order("-timestamp").get()
    
    tags = TagStats.all().filter("developer_stats =", stats)
    tags = tags.order("-total").fetch(20)
    
    return render_to_response("stats/stats.html",
                              {'stats': stats,
                               'countries': countries,
                               'tags': tags}, 
                              RequestContext(request))

