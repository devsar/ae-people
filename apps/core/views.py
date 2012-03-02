from django import forms 

from django.shortcuts import render_to_response
from django.template import RequestContext
from users.models import Developer
from country.models import Country

def index(request):
    query = Developer.all()
    query.order('-sign_up_date')
    developers = query.fetch(100)
    
    countries = Country.all().filter("total >", 0).fetch(300)
    countries = sorted(countries, key=lambda x: unicode(x.name))
    
    return render_to_response('index.html',
                              {'developers': developers,
                               'countries': countries },
                              RequestContext(request))

def about(request):    
  try:
    import math, logging

    p1lat = 0.954897469667
    p2lat = 0.954897473513
    p1lon = 0.357966544383
    p2lon = 0.357966544383

    logging.error(math.acos(math.sin(p1lat) * math.sin(p2lat) + math.cos(p1lat) * math.cos(p2lat) * math.cos(p2lon - p1lon)))
  except:
    logging.exception()

  return render_to_response('about.html', {}, RequestContext(request))

class SearchForm(forms.Form):
    query = forms.CharField(min_length=3, required=True, help_text="use 'OR', 'AND', 'NOT', wildcard(*) and combining them to perform the search")

def search(request):
    params = {}
    form = SearchForm(request.GET or None)
    if form.is_valid():
        query = form.cleaned_data['query']
        params['developers'] = Developer.search(query=query)
    
    params['form'] = form
    
    return render_to_response('search.html', params, RequestContext(request))
