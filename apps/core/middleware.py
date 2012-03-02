import re
import logging
import traceback


from google.appengine.api.mail import EmailMessage
from django.conf import settings

class UserMiddleware:

    def process_request(self, request):

        url = request.get_full_path()
        
        match = re.search(r"/user/(?P<username>[\w\d\_]+)/.*", url)
        
        if match:
            username = match.group('username')
            user = User.all().filter('username =', username).get()
            request.user_actual = user
        else:
            request.user_actual = None
    
    
class ExceptionMiddleware:
    
    def process_exception(self, request, exception):
        logging.exception('exception!')
        message = EmailMessage()
        message.sender = settings.DEFAULT_FROM_EMAIL
        message.to = [admin[1] for admin in settings.ADMINS]
        message.subject = 'exception at %s' % request.path
        message.body = """
URL: %(url)s
Exception:
%(traceback)s

---

User: %(user)s 
Email: %(email)s

---

REQUEST META:
%(META)s
        """ % {
            'url': request.build_absolute_uri(request.get_full_path()),
            'traceback': traceback.format_exc(),
            'user': request.user,
            'email': request.user.email if request.user.is_authenticated() else None,
            'META': request.META
        }
        message.check_initialized()
        message.send()
        
        return None
