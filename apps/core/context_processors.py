
from django.conf import settings

def ae_vars(request):
    p = {
        'FUSIONTABLE_ID': settings.FUSIONTABLE_ID,
    }
    
    return p