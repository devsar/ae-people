'''
Created on 10/12/2009

@author: martin
'''
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^update/$', 'stats.views.update_stats' , name="stats_update"),    
    url(r'^$', 'stats.views.view_stats' , name="stats_view"),    
)
