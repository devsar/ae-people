# Copyright 2010 Livemade.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from django.views.generic.simple import direct_to_template
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^$', 'core.views.index', name="core_index"),
    (r'^about/$', 'core.views.about'),
    (r'^search/$', 'core.views.search'),
    (r'^users/', include("users.urls")),
    (r'^country/', include("country.urls")),
    (r'^stats/', include("stats.urls")),
)
