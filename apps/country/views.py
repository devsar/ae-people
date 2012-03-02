"""
    Country views
"""
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response
from django.template import RequestContext

from google.appengine.api.labs import taskqueue

from country.models import Country, COUNTRIES_CODE
from users.models import Developer

def chunks(l, n):
    """ 
    Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

def update_country(request, country_code=None):
    """
    Update country if given or all if not
    """
    if country_code:
        Country.update(country_code)
        return HttpResponse("")
    
    #queue update for all countries  
    queue = taskqueue.Queue()
    tasks = [taskqueue.Task(url=reverse("country_update_country", kwargs={'country_code': str(country)})) 
             for country in COUNTRIES_CODE]
    
    for chunk in chunks(tasks, 100):
        queue.add(chunk)
    return HttpResponse("")


def developers_by_country(request, country_code):
    """
        Show developers for a country
    """
    country_code = country_code.upper()
    developers = Developer.all().filter('country =', country_code).fetch(1000)
    country = Country.get_by_key_name(country_code)
    if country is None:
        raise Http404
    return render_to_response('country/country.html', {'developers': developers, 'country': country }, RequestContext(request))

