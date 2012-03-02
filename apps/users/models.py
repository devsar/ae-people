import logging

from appengine_django.models import BaseModel
from google.appengine.ext import db
from google.appengine.api import taskqueue

from django.template.defaultfilters import striptags
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from aetycoon import TransformProperty
from geo.geomodel import GeoModel

from country.models import COUNTRIES, COUNTRIES_CODE

class Developer(BaseModel, GeoModel):
    user = db.ReferenceProperty(User)
    alias = db.StringProperty(required=True)
    email_contact = db.EmailProperty()
    
    first_name = db.StringProperty(required=True)
    last_name = db.StringProperty(required=True)
    photo = db.BlobProperty()
    
    location = db.GeoPtProperty(required=True)
    location_geocells = db.StringListProperty()
    location_description = db.StringProperty()
    
    country = db.StringProperty(required=True,default='AR',choices=COUNTRIES_CODE)
                                
    phone = db.PhoneNumberProperty()
    personal_blog = db.LinkProperty()
    personal_page = db.LinkProperty()
    public_contact_information = db.BooleanProperty(default=False)
    
    sign_up_date = db.DateTimeProperty(auto_now_add=True)
    last_update = db.DateTimeProperty(auto_now=True)
    last_login = TransformProperty(user, lambda x: x.last_login if x else None)
    
    about_me = db.TextProperty()
    
    python_sdk = db.BooleanProperty()
    java_sdk = db.BooleanProperty()
    tags = db.StringListProperty()
    
    
    def getname(self):
        return "%s %s" % (self.first_name.capitalize(), self.last_name.capitalize())

    def get_country(self):
        countries = dict(COUNTRIES)
        return u"%s" % (countries[self.country])
    
    def put(self, * args, ** kwargs):
        self.update_location()
        super(Developer, self).put(* args, ** kwargs)

    def delete(self, * args, ** kwargs):
        #queue ft update
        taskqueue.add(url=reverse("users_fusiontable_delete", args=[str(self.alias)]))
        super(Developer, self).delete(* args, ** kwargs)



def get_developer(self):    
    if hasattr(self, '_developer') is False:
        self._developer = Developer.all().filter("user =", self).get()
    return self._developer

User.developer = property(get_developer)

class NetworkLink(BaseModel):
    network = db.StringProperty()
    username = db.StringProperty()
    developer = db.ReferenceProperty(Developer)

