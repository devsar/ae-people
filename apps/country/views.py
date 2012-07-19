"""
    Country views
"""
import logging
import os

from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response
from django.template import RequestContext

from google.appengine.api.labs import taskqueue

from country.models import Country, COUNTRIES_CODE
from users.models import Developer

def update_country(request, run=None):
    """
    Update country if given or all if not
    """
    logging.info("%s" % os.environ.keys())
    if "run" in request.POST:
        for country_code in COUNTRIES_CODE:
            logging.info("processing: %s" % country_code)
            Country.update(country_code)
        return HttpResponse("")
    else:
        #put in a taskqueue to 
        taskqueue.add(url=reverse("country_update_country"), params={'run': "1"})

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

