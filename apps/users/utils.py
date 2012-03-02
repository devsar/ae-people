'''
Created on 16/11/2009

@author: sebastian
'''
from django import forms
from django.utils.safestring import mark_safe
from django.template import Context, Template

class LocationWidget(forms.widgets.Widget):
    def __init__(self, *args, **kw):
        super(LocationWidget, self).__init__(*args, **kw)
        self.inner_widget = forms.widgets.HiddenInput()

    def render(self, name, value, *args, **kwargs):
        
        html = self.inner_widget.render("%s" % name, None, dict(id='%s_id' % name))
        html += "<div id=\"map_%s\" style=\"height: 500px\"></div>" % name
        html_js = Template('''
        </script>
        <script type="text/javascript">
            //<![CDATA[
            google.load("maps", "2");
            var marker_{{ name|cut:'-' }} = null;
            var map_{{ name|cut:'-' }} = null ;
            $(document).ready(function () {
                if (GBrowserIsCompatible()) {
                    map_{{ name|cut:'-' }} = new google.maps.Map2(document.getElementById("map_{{ name }}"));
                    {% if not value %}
                    if (google.loader.ClientLocation){
                        var center = new google.maps.LatLng(
                            google.loader.ClientLocation.latitude,
                            google.loader.ClientLocation.longitude);
                        var zoom = 6;
                        map_{{ name|cut:'-' }}.setCenter(center, zoom);
                        marker_{{ name|cut:'-' }} = new GMarker(new GLatLng(google.loader.ClientLocation.latitude, google.loader.ClientLocation.longitude), {draggable: true});
                    } 
                    else{
                        map_{{ name|cut:'-' }}.setCenter(new GLatLng(0.0, 0.0), 2);
                        marker_{{ name|cut:'-' }} = new GMarker(new GLatLng(0.0,0.0), {draggable: true});
                    }
                    {% else %}
                    map_{{ name|cut:'-' }}.setCenter(new GLatLng({{ value }}), 6);
                    marker_{{ name|cut:'-' }} = new GMarker(new GLatLng({{ value }}), {draggable: true});
                    {% endif %}
                    
                    map_{{ name|cut:'-' }}.addOverlay(marker_{{ name|cut:'-' }});
                    map_{{ name|cut:'-' }}.addControl(new GLargeMapControl());
                    $('#{{ name }}_id')[0].value = marker_{{ name|cut:'-' }}.getLatLng().lat() + "," + marker_{{ name|cut:'-' }}.getLatLng().lng();
                    
                    GEvent.addListener(marker_{{ name|cut:'-' }}, "dragend", function() {
                        var point = marker_{{ name|cut:'-' }}.getLatLng();
                        $('#{{ name }}_id')[0].value = point.lat() + "," + point.lng();
                    });
                }});
            $(document).unload(function () {GUnload()});
            //]]>
        </script>
        {{ html|safe }}
        ''')
        output = html_js.render(Context({
            'name': name,
            'value': value,
            'html': html
        }))
        return mark_safe(output)


class LocationField(forms.Field):
    widget = LocationWidget

    def clean(self, value):
        try:
            a, b = value.split(',')
            lat, lng = float(a), float(b)
            return "%s,%s" % (lat, lng)
        except ValueError:
            raise forms.ValidationError("Invalid location field value")

        