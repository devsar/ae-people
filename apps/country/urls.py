'''
Created on 10/12/2009

@author: martin
'''
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^update/$', 'country.views.update_country' , name="country_update_country"),
    url(r'^(?P<country_code>[\w]+)/$', 'country.views.developers_by_country' , name="country_developers"),    
)
