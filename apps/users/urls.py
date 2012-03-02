'''
Created on 10/12/2009

@author: martin
'''
from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('',
    url(r'^sign_up/$', 'users.views.sign_up', name="users_sign_up"),
    url(r'^check_profile/$', 'users.views.check_profile', name="users_check_profile"),
    url(r'^developers_json/$', 'users.views.developers_json' , name="users_developers_json"),
    url(r'^avatar/(?P<developer_id>[\d]+)/$', 'users.views.avatar' , name="users_avatar"),
    url(r'^avatar_change/$', 'users.views.avatar_change' , name="users_avatar_change"),
    url(r'^tag/(?P<tag>[^/]+)/$', 'users.views.developers_by_tag' , name="users_by_tag"),
    url(r'^sitemap/$', 'users.views.developer_sitemap'),
    url(r'^fusiontable_build/$', 'users.views.fusiontable_build', name="users_fusiontable_build"),
    url(r'^fusiontable_insert/(?P<key>[^/]+)/$', 'users.views.fusiontable_insert', name="users_fusiontable_insert"),
    url(r'^fusiontable_delete/(?P<alias>[^/]+)/$', 'users.views.fusiontable_delete', name="users_fusiontable_delete"),
    url(r'^(?P<alias>[\-\d\w]+)/edit/$', 'users.views.edit_profile', name="users_edit"),
    url(r'^(?P<alias>[\-\d\w]+)/$', 'users.views.view_profile', name="users_profile"),

)
