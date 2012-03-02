import logging

from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson
from django.utils.translation import ugettext_lazy as _

from geo import geotypes

from google.appengine.api import taskqueue

from users.forms import DeveloperForm, SignUpStep1Form, SignUpStep2Form, SignUpStep3Form, SignUpWizard
from users.models import Developer
from django.template.defaultfilters import striptags



logger = logging.getLogger('users.views')

@login_required
def check_profile(request):
    developer = Developer.all().filter('user =', request.user).get()
    if developer is None:
        return HttpResponseRedirect(reverse("users_sign_up"))
    else:
        next = request.GET.get('next', None)
        if next:
            return HttpResponseRedirect(next)
        else:
            return HttpResponseRedirect('/')
        
@login_required
def sign_up(request):
    """ Sign_up a new developer """
    #just in case is already registered 
    if Developer.all().filter("user =", request.user).get():
        return HttpResponseRedirect("/")
    
    return SignUpWizard([SignUpStep1Form, SignUpStep2Form, SignUpStep3Form])(request) 

@login_required
def edit_profile(request, alias=None):
    
    if alias != request.user.developer.alias:
        return render_to_response('error.html', 
                                  {'message': "Permiso denegado" }, RequestContext(request))
    
    developer = Developer.all().filter('alias =', alias).get()    
    if developer is None:
        return render_to_response('error.html', 
                                  {'message': "Usuario inexistente" }, RequestContext(request))
                    
    if request.method == 'POST':
        form = DeveloperForm(request.POST, instance=developer)
        if form.is_valid():            
            developer = form.save(commit=False)
            if request.FILES.has_key('photo'):
                developer.photo = request.FILES['photo'].read()
            developer.put()
            taskqueue.add(url=reverse("users_fusiontable_insert", args=[str(developer.key())]))
            return HttpResponseRedirect(reverse('users_profile', args=[alias]))
    else:
        form = DeveloperForm(instance=developer)
    
    return render_to_response('users/edit.html', {'form' : form}, RequestContext(request))
         

def view_profile(request, alias):
    """
        Show developer profile page
    """
    developer = Developer.all().filter('alias =', alias).get()
    if developer is None:
        raise Http404
    
    try:
        near_me = Developer.proximity_fetch(Developer.all().filter('country =', developer.country).filter('alias !=', developer.alias),
                                        geotypes.Point(developer.location.lat, developer.location.lon),
                                        max_results=20,
                                        max_distance=1000000)
    except ValueError:
        logging.exception("problem resolving near users for lat/long %s %s" % (developer.location.lat, developer.location.lon))
        near_me = []
    
    params = {
        'developer': developer, 
        'near_me': near_me
    }
    
    if developer.email_contact:
        try:
            from recaptcha.client import mailhide
            params['email_contact'] = mailhide.ashtml(developer.email_contact, 
                                                  settings.MAILHIDE_PUBLIC, 
                                                  settings.MAILHIDE_PRIVATE)
        except:
            logger.exception("problems")
        
    return render_to_response('users/profile.html', params, RequestContext(request))

    
def developers_json(request):
    
    def dump_developer(d):
        return {"lat": d.location.lat, "lon": d.location.lon }
    data = simplejson.dumps([dump_developer(d) for d in  Developer.all()])
    
    return HttpResponse(data)

def avatar(request, developer_id):
    developer = Developer.get_by_id(int(developer_id))
    if developer is None:
        raise Http404
    
    if developer.photo is None:
        return HttpResponseRedirect("/static/images/no_avatar.png")
    
    return HttpResponse(developer.photo, mimetype="image/jpeg")

def developers_by_tag(request, tag):
    developers = Developer.all().filter('tags =', tag).fetch(100)
    return render_to_response('users/tags.html', {'developers': developers, 'tag': tag }, RequestContext(request))


@login_required
def avatar_change(request):
    """
    Change user avatar
    """
    try:
        from google.appengine.api import images
        developer = request.user.developer
        if request.method == 'POST':
            if request.FILES.has_key('avatar'):
                
                im = images.Image(request.FILES['avatar'].read())
                
                if im.width > im.height:
                    extra = float(im.width - im.height) / im.width
                    keep =  float(im.height) / im.width
                    im.crop(extra/2, 0.0, extra/2 + keep, 1.0)
                elif im.height > im.width:
                    extra = float(im.height - im.width) / im.height
                    keep =  float(im.width) / im.height 
                    im.crop(0.0, extra/2, 1.0, keep + extra/2)
                    
                im.resize(200, 200)
                normal = im.execute_transforms(output_encoding=images.JPEG)
                                
                developer.photo = normal
                developer.put()
    
                request.flash['message'] = unicode(_("Avatar changed"))
                request.flash['severity'] = "success"
                return HttpResponse("OK")
            
        return render_to_response("users/avatar_change.html", 
                                  { },
                                  RequestContext(request))
    except:
        logger.exception("")
        raise
    

def developer_sitemap(request):
    
    
    sitemap = """<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">"""
    
    for dev in Developer.all():
       sitemap += """
       <url>
          <loc>%s%s</loc>
          <lastmod>2010-04-21</lastmod>
          <changefreq>monthly</changefreq>
          <priority>0.8</priority>
       </url>
       """ % (settings.SITE_URL, reverse('users_profile', args=[dev.alias]))
    sitemap += "</urlset>"
    return  HttpResponse(sitemap)



def fusiontable_build(request):
    """
        Update the fusion table
        
        table = {'developers': 
            {
                'alias': 'STRING', 
                'name': 'STRING', 
                'location': 'LOCATION', 
                'address': 'STRING', 
                'profile': 'STRING',
                'country': 'STRING',
                'about_me': 'STRING',
             }
        }
        #created with
        tableid = int(ft_client.query(SQL().createTable(table)).split("\n")[1])                           
    """
    FETCH = 10
    
    cursor = request.POST.get('cursor', None)
    
    query = Developer.all()
    
    if cursor is None:
        #first call truncate table
        from ft import ftclient
        from ft.sql.sqlbuilder import SQL
        from ft.authorization.clientlogin import ClientLogin
        
        token = ClientLogin().authorize(settings.GOOGLE_USER, settings.GOOGLE_PASSWORD)
        ft_client = ftclient.ClientLoginFTClient(token)
        ft_client.query("DELETE FROM %d" % settings.FUSIONTABLE_ID)
    else:
        query = query.with_cursor(cursor)
    
    developers = query.fetch(FETCH)
        
    for i, d in enumerate(developers):
        taskqueue.add(url=reverse("users_fusiontable_insert", args=[str(d.key())]), countdown=i)
        
    if len(developers) == FETCH:
        taskqueue.add(url=reverse("users_fusiontable_build"), params={'cursor': query.cursor()}, countdown=40)

            
    return HttpResponse("")


def fusiontable_insert(request, key):
    import textile
    
    from ft import ftclient
    from ft.sql.sqlbuilder import SQL
    from ft.authorization.clientlogin import ClientLogin
    
    d = Developer.get(key)
    if d is None:
        raise Http404
    
    token = ClientLogin().authorize(settings.GOOGLE_USER, settings.GOOGLE_PASSWORD)
    ft_client = ftclient.ClientLoginFTClient(token)
    
    try:
        rowid = int(ft_client.query(SQL().select(settings.FUSIONTABLE_ID, ['rowid'], "alias='%s'" % d.alias)).split("\n")[1])
        ft_client.query(SQL().delete(settings.FUSIONTABLE_ID, rowid))
    except (ValueError):
        pass
    
    about_me = striptags(textile.textile(d.about_me or ""))[:200]
    if len(about_me) == 200:
        about_me += "..."
    
    u = {
         'alias': d.alias,
         'name': d.getname(),
         'location': "%0.3f,%0.3f" % (d.location.lat, d.location.lon), 
         'address': d.location_description or "", 
         'country': d.get_country(), 
         'avatar': reverse('users_avatar', args=[d.key().id()]), 
         'profile': reverse('users_profile', args=[d.alias]),
         'about_me': about_me
    }
    
    ft_client.query(SQL().insert(settings.FUSIONTABLE_ID, u))
    
    return HttpResponse("")


def fusiontable_delete(request, alias):

    from ft import ftclient
    from ft.sql.sqlbuilder import SQL
    from ft.authorization.clientlogin import ClientLogin


    token = ClientLogin().authorize(settings.GOOGLE_USER, settings.GOOGLE_PASSWORD)
    ft_client = ftclient.ClientLoginFTClient(token)

    try:
        rowid = int(ft_client.query(SQL().select(settings.FUSIONTABLE_ID, ['rowid'], "alias='%s'" % alias)).split("\n")[1])
        ft_client.query(SQL().delete(settings.FUSIONTABLE_ID, rowid))
    except (ValueError):
        pass

    return HttpResponse("")

