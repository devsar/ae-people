import re

from django import forms
from django.core.urlresolvers import reverse
from django.contrib.formtools.wizard import FormWizard
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.utils.translation import ugettext_lazy as _

from google.appengine.ext.db import djangoforms
from google.appengine.api.labs import taskqueue


from uni_form.helpers import FormHelper, Submit
from uni_form.helpers import Layout, Fieldset, Row

from models import Developer
from users.utils import LocationField

from country.models import COUNTRIES


class DeveloperForm(djangoforms.ModelForm):

    #geolocation = LocationField()
    about_me = forms.CharField(widget=forms.Textarea, 
                               help_text="accepts textile markup (<a target='_new' href='http://textile.thresholdstate.com/'>reference</a>)", 
                               required=False)
    location = LocationField()
    country = forms.ChoiceField(choices=COUNTRIES)
    tags = forms.CharField(help_text=_("space separated"))
    
    class Meta:
        model = Developer
        #fields = ['alias', 'email_contact', 'first_name', 'last_name', 'location', 'photo']
        exclude = ('_class', 'user', 'last_login', 'sign_up_date', 'location_geocells', 'photo')
    
    def clean_tags(self):
        tags = self.cleaned_data['tags']
        if "," in tags:
            tags = [tag.strip().replace(" ","-") for tag in tags.split(",")]
        else:
            tags = tags.split(" ")
            
        return filter(len, map(lambda x: x.strip().lower(), tags))
    
    def clean_alias(self):
        alias = self.cleaned_data["alias"].strip()
        
        if re.match("^([\w\d_]+)$", alias) is None:
            raise forms.ValidationError(_("alias not valid, use only letters, numbers or underscores"))
        
        if self.instance and self.instance.alias == alias:
            return alias
        
        if Developer.all(keys_only=True).filter("alias =", alias).get(): 
            raise forms.ValidationError(_("alias not available"))
        
        return alias
    
    # Attach a formHelper to your forms class.
    helper = FormHelper()

    # create the layout object
    layout = Layout(
                    # first fieldset shows the company
                    Fieldset('Basic', 'alias',
                             Row('first_name','last_name'),
                             'about_me',
                             'python_sdk',
                             'java_sdk',
                             'tags', css_class="developer_basic"),

                    # second fieldset shows the contact info
                    Fieldset('Contact details',
                            'public_contact_information',
                            'email_contact',
                            'phone',
                            'personal_blog',
                            'personal_page',
                            css_class="developer_contact_details"),
                    Fieldset('Location',
                            'country', 
                            'location_description',
                            'location',
                            css_class="developer_contact_details")
                    )

    helper.add_layout(layout)

    submit = Submit('save',_('Save'))
    helper.add_input(submit)

class SignUpStep1Form(forms.Form):
    alias = forms.CharField()
    first_name = forms.CharField()
    last_name = forms.CharField()
    
    def clean_alias(self):
        alias = self.cleaned_data["alias"].strip()
        
        if re.match("^([\w\d_]+)$", alias) is None:
            raise forms.ValidationError(_("alias not valid, use only letters, numbers or underscores"))
                
        if Developer.all(keys_only=True).filter("alias =", alias).get(): 
            raise forms.ValidationError(_("alias not available"))
        
        return alias

class SignUpStep2Form(forms.Form):
    SDK_CHOICES = (
        ('python', 'python'), 
        ('java', 'java')
    )
    
    email_contact = forms.CharField(help_text="protected with reCAPTCHA Mailhide", required=False)
    phone = forms.CharField(required=False)
    personal_blog = forms.URLField(required=False)
    personal_page = forms.URLField(required=False)
    
    about_me = forms.CharField(widget=forms.Textarea, 
                               help_text="accepts textile markup (<a target='_new' href='http://textile.thresholdstate.com/'>reference</a>)", 
                               required=False)
    sdks = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=SDK_CHOICES,help_text="which SDKs you use?", required=False)
    tags = forms.CharField(help_text=_("space separated"), required=False)

    def clean_tags(self):
        tags = self.cleaned_data['tags']
        if "," in tags:
            tags = [tag.strip().replace(" ","-") for tag in tags.split(",")]
        else:
            tags = tags.split(" ")
            
        return filter(len, map(lambda x: x.strip().lower(), tags))

class SignUpStep3Form(forms.Form):
    location = LocationField()  
    location_description = forms.CharField()
    country = forms.ChoiceField(choices=COUNTRIES)


class SignUpWizard(FormWizard):    
    def get_template(self, step):
        return 'users/sign_up_%s.html' % step

    def done(self, request, form_list):
        
        cleaned_data = {}
        [cleaned_data.update(form.cleaned_data) for form in form_list]
        
        import logging
        logging.info(cleaned_data)
        
        form = DeveloperForm(cleaned_data)
        developer = Developer(
          user = request.user,
          alias = cleaned_data['alias'], 
          email_contact = cleaned_data['email_contact'] or None,
          first_name = cleaned_data['first_name'],
          last_name = cleaned_data['last_name'],                                
          location = cleaned_data['location'] or None,
          location_description = cleaned_data['location_description'] or None,
          country = cleaned_data['country'],
          phone = cleaned_data['phone'] or None,
          personal_blog = cleaned_data['personal_blog'] or None,
          personal_page = cleaned_data['personal_page'] or None,
          public_contact_information = True,
          about_me = cleaned_data['about_me'] or None,
          python_sdk = "python" in cleaned_data['sdks'],
          java_sdk = "java" in cleaned_data['sdks'],
          tags = cleaned_data['tags'] or []
        )
        developer.put()
        
        taskqueue.add(url=reverse("users_fusiontable_insert", args=[str(developer.key())]))
        taskqueue.add(url=reverse("country_update_country", kwargs={'country_code': developer.country}))
        
        request.flash['message'] = unicode(_("Welcome!"))
        request.flash['severity'] = "success"
        
        return HttpResponseRedirect(reverse('users_avatar_change'))
