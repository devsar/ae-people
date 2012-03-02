import logging

from google.appengine.api import users

from django.contrib.auth.models import User
from django.test import TestCase

from users.models import Developer

class UsersTest(TestCase):
  def setUp(self):
    appengine_user = users.User("test@example.com", _user_id="test@example.com")
    logging.info(appengine_user)
    django_user = User.get_djangouser_for_user(appengine_user)

    logging.info(django_user)

    self.developer = Developer(user=django_user, alias="test", first_name="test", last_name="test", location="0,0")
    self.developer.put()

  def testRemove(self):
    self.developer.delete()

